// Copyright 2026 The OpenSandbox Authors
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

package fastsandboxnft

import (
	"context"
	"fmt"
	"net/netip"
	"strings"
	"time"

	"github.com/alibaba/opensandbox/egress/pkg/log"
	"github.com/alibaba/opensandbox/egress/pkg/nftables"
	"github.com/alibaba/opensandbox/egress/pkg/telemetry"
	"github.com/alibaba/opensandbox/internal/safego"
)

// UpstreamProxyEndpoint describes the chained upstream CONNECT proxy under
// the fast-sandbox enforcement model: infrastructure that sandbox traffic
// must never reach directly. A sandbox CONNECTing the proxy itself could
// relay to otherwise-denied destinations on unintercepted ports, so the
// endpoint is dropped for all subjects regardless of policy — including
// default-allow subjects and subjects whose policy happens to allow the
// proxy address.
type UpstreamProxyEndpoint struct {
	Port int
	// LiteralIPs seeds the drop sets permanently. Hostname endpoints start
	// empty and are filled via AddUpstreamProxyIPs as the egress resolves
	// the infra domain.
	LiteralIPs []netip.Addr
}

// upstreamProxySetFor maps an address to its drop-set name ("" when invalid).
func upstreamProxySetFor(addr netip.Addr) string {
	if addr.Is4() {
		return upstreamProxyV4Set
	}
	if addr.Is6() {
		return upstreamProxyV6Set
	}
	return ""
}

// writeUpstreamProxyStatic renders the drop sets with literal (permanent)
// and DNS-learned (mirrored, remaining TTL) elements plus the profile-wide
// drop rules. Callers must hold a.mu (the mirror is pruned in place).
// The forward rules sit BEFORE the dispatch chain's established accept and
// every per-subject jump: no subject policy — default-allow included — may
// CONNECT the proxy directly, and stale established flows from a previous
// egress generation (one without an upstream proxy) must not survive a
// restart either. The mitmdump dial is locally generated (OUTPUT path), so
// it never matches these forward rules.
func (a *Applier) writeUpstreamProxyStatic(b *strings.Builder) {
	ep := a.opts.UpstreamProxy
	fmt.Fprintf(b, "add set inet %s %s { type ipv4_addr; flags timeout; }\n", TableName, upstreamProxyV4Set)
	fmt.Fprintf(b, "add set inet %s %s { type ipv6_addr; flags timeout; }\n", TableName, upstreamProxyV6Set)
	for _, ip := range ep.LiteralIPs {
		addr := ip.Unmap()
		set := upstreamProxySetFor(addr)
		if set == "" {
			continue
		}
		// permanent element (no timeout): literal endpoints are not DNS-learned
		fmt.Fprintf(b, "add element inet %s %s { %s }\n", TableName, set, addr)
	}
	now := a.now()
	for addr, expires := range a.upstreamIPs {
		set := upstreamProxySetFor(addr)
		if set == "" {
			delete(a.upstreamIPs, addr)
			continue
		}
		if !expires.After(now) {
			delete(a.upstreamIPs, addr)
			continue
		}
		remaining := int((expires.Sub(now) + time.Second - 1) / time.Second)
		fmt.Fprintf(b, "add element inet %s %s { %s timeout %ds }\n", TableName, set, addr, remaining)
	}
	fmt.Fprintf(b, "add rule inet %s %s ip daddr @%s tcp dport %d drop\n", TableName, dispatchChain, upstreamProxyV4Set, ep.Port)
	fmt.Fprintf(b, "add rule inet %s %s ip6 daddr @%s tcp dport %d drop\n", TableName, dispatchChain, upstreamProxyV6Set, ep.Port)
}

// writeUpstreamProxyInputRules renders the input-path containment for
// intercepted traffic: a CONNECT whose ORIGINAL destination is the proxy
// endpoint (its port inside the intercepted set) is dropped before the
// input chain's established accept. Only emitted with MITM enabled, after
// the input chain exists and before its first rule.
func (a *Applier) writeUpstreamProxyInputRules(b *strings.Builder) {
	ep := a.opts.UpstreamProxy
	fmt.Fprintf(b, "add rule inet %s %s ct status dnat ct original ip daddr @%s ct original proto-dst %d drop\n",
		TableName, inputChain, upstreamProxyV4Set, ep.Port)
	fmt.Fprintf(b, "add rule inet %s %s ct status dnat ct original ip6 daddr @%s ct original proto-dst %d drop\n",
		TableName, inputChain, upstreamProxyV6Set, ep.Port)
}

// AddUpstreamProxyIPs feeds DNS-learned proxy addresses into the drop sets.
// Elements carry the (clamped) answer TTL like the sidecar profile's scoped
// sets; the mirror is committed only after a successful apply so table
// rebuilds stay deterministic. No-op when no upstream proxy is configured.
func (a *Applier) AddUpstreamProxyIPs(ctx context.Context, ips []nftables.ResolvedIP) error {
	if a.opts.UpstreamProxy == nil || len(ips) == 0 {
		return nil
	}
	var script strings.Builder
	expiry := make(map[netip.Addr]time.Time, len(ips))
	now := a.now()
	for _, r := range ips {
		addr := r.Addr.Unmap()
		set := upstreamProxySetFor(addr)
		if set == "" {
			continue
		}
		ttl := clampTTL(r.TTL)
		// idempotent add first (a fresh table after a rebuild may not carry
		// the element), then delete + re-add with the TTL — the same pattern
		// as the sidecar manager's AddUpstreamProxyIPs.
		fmt.Fprintf(&script, "add element inet %s %s { %s }\n", TableName, set, addr)
		fmt.Fprintf(&script, "delete element inet %s %s { %s }\n", TableName, set, addr)
		fmt.Fprintf(&script, "add element inet %s %s { %s timeout %ds }\n", TableName, set, addr, int(ttl/time.Second))
		expiry[addr] = now.Add(ttl)
	}
	if script.Len() == 0 {
		return nil
	}
	a.mu.Lock()
	defer a.mu.Unlock()
	if _, err := a.run(ctx, script.String()); err != nil {
		telemetry.RecordNftablesUpdateFailed(telemetry.NftOpUpstreamProxyAdd)
		return err
	}
	for addr, at := range expiry {
		a.upstreamIPs[addr] = at
	}
	telemetry.RecordNftablesUpdate()
	return nil
}

// upstreamProxyRefreshInterval is how often the egress re-resolves the
// upstream proxy hostname to renew the drop-set elements. One query per
// fastlet per tick; the clamped element TTL (>= 60s) leaves a full grace
// interval before containment could lapse on a transient failure.
const upstreamProxyRefreshInterval = 30 * time.Second

// StartUpstreamProxyRefresh re-resolves the upstream proxy hostname through
// lookup and feeds the answers to AddUpstreamProxyIPs, so the drop sets stay
// seeded even when no sandbox ever queries the name: sandbox lookups keep
// them fresh through the dnsproxy infra-domain callback, but nothing
// guarantees such queries. Failures are logged and retried next tick; an
// element whose renewal keeps failing eventually expires (fail-open for
// that address), which is acceptable only because the shared mitmproxy's
// own chained dials are then failing equally. Literal endpoints need no
// loop (their elements are permanent).
func (a *Applier) StartUpstreamProxyRefresh(ctx context.Context, domain string, lookup func(context.Context, string) ([]nftables.ResolvedIP, error)) {
	safego.Go(func() {
		resolve := func() {
			resolveCtx, cancel := context.WithTimeout(ctx, 5*time.Second)
			defer cancel()
			ips, err := lookup(resolveCtx, domain)
			if err != nil {
				log.Warnf("fastsandboxnft: upstream proxy resolve %q failed: %v", domain, err)
				return
			}
			if len(ips) == 0 {
				log.Warnf("fastsandboxnft: upstream proxy %q resolved to no addresses", domain)
				return
			}
			if err := a.AddUpstreamProxyIPs(resolveCtx, ips); err != nil {
				log.Warnf("fastsandboxnft: upstream proxy nft update for %q failed: %v", domain, err)
			}
		}
		// Seed the drop sets immediately so containment is active before the
		// first sandbox registers.
		resolve()
		ticker := time.NewTicker(upstreamProxyRefreshInterval)
		defer ticker.Stop()
		for {
			select {
			case <-ctx.Done():
				return
			case <-ticker.C:
				resolve()
			}
		}
	})
}
