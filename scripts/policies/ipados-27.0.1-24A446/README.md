Bring-up dummy root policies for cupid (iPhone17,2, iOS 27.0.1 24A446).

The build-sheng-source-storage.py policy lookup is keyed by the OS build id
(`scripts/policies/*24A446`), and the assembled tree already contains UniXNU's
own `ipados-27.0.1-24A446` directory (prelink data), so this device directory
uses the same name to replace that directory's policy inputs instead of
adding a second `*24A446` match, which the builder refuses.

The 544-byte manifests carry the real cupid OS/SystemOS image digests and a
placeholder 395-byte anchor. They exist only to pass the builder's digest,
volume-UUID and key checks. The cupid kernel forces NATIVE_VERIFIED_BLOCK=0
and SourceRootPolicies returns true, so these signatures are never read.
