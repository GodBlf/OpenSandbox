// Copyright 2026 The OpenSandbox Authors. Licensed under the Apache License, Version 2.0.
package com.alibaba.opensandbox.sandbox.domain.models.sandboxes

import java.time.Duration
import java.time.OffsetDateTime

/** Each non-null field replaces the inherited source setting completely. */
data class ForkOverrides
    @JvmOverloads
    constructor(
        val env: Map<String, String>? = null,
        val resourceLimits: Map<String, String>? = null,
        val resourceRequests: Map<String, String>? = null,
        val networkPolicy: NetworkPolicy? = null,
        val metadata: Map<String, String>? = null,
        val entrypoint: List<String>? = null,
    )

data class ForkRequest
    @JvmOverloads
    constructor(
        val timeout: Duration,
        val overrides: ForkOverrides? = null,
    ) {
        init {
            require(timeout >= Duration.ofSeconds(60) && timeout.nano == 0 && timeout.seconds <= Int.MAX_VALUE) {
                "Fork timeout must be whole seconds, at least 60 and fit the API integer range."
            }
        }
    }

data class ForkStatus(val state: String, val reason: String?, val message: String?)

data class ForkOperation(
    val id: String,
    val sourceSandboxId: String,
    val status: ForkStatus,
    val snapshotId: String?,
    val sandboxId: String?,
    val createdAt: OffsetDateTime,
    val updatedAt: OffsetDateTime,
    val cleanupPending: Boolean,
)

class ForkWaitTimeoutException(val forkId: String) :
    RuntimeException("Timed out waiting for fork $forkId; the server operation continues.")
