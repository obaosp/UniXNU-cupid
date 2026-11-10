# Panic — first iOS 26 XNU start (2026-11-10)

Image: `boot-v4-ios26.img`, sha256
`c5b9f6203ce1b715d42eba6bfb7df781c0029a8e4f5da55e003d94b7bbf31ab0`
(run `42703962893`, commit `0553985`).

Screenshot: `%USERPROFILE%\Downloads\20261110_075017.jpg`.

```
fileset: original component called an unmapped kernel function
from 0xfffffff008d05be8 (x0 0xfffffff7a334bbc x1 0x0)
frames ffffff00aea041c ffffff008d05be8 fffff008d032bc ff...
Pages=0x000000000078f35
free=0x000000000078ff5
```

Decoded with `tools/diagnose-unmapped-call.py` against the emitted
`kernel.macho` (from the boot image payload) and the pinned 26.5.2
kernelcache:

```
caller:          com.apple.security.AppleImage4/__TEXT_EXEC
call site:       0xfffffff008d05be4 bl -> 0xfffffff00aea03ec (stub)
original callee: 0xfffffff00abda26c (com.apple.kernel/__TEXT_EXEC, 240 bytes)
```

The target is AppleImage4's one-time security-flag initializer. It reads the
init byte at `0x7cd6ee8`, computes a flag word from the security-mode struct at
`0x7cd7010/0x7cd7030`, and caches status 2 + flags at
`0x7cd6eec/0x7cd6ef0`. The native `__DATA_CONST` placement overwrites those
globals, so the original body cannot run.

Fix: bind `0xabda26c` to `_unixnu_apple_image4_flags`, the same shim used for
24A446: write status 2 and flags 0, leave the return value ignored (the
AppleImage4 wrapper reads the status out-pointer). The shim is added by
`patches/xnu/image4-flags-shim.patch`.
