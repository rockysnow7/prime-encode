*prime-encode* is a compression algorithm based around prime factorisation.
Specifically, each pair of characters in the input is replaced with a semiprime, almost halving
file sizes.
Note that this uses hashing so is only lossless if all hashes are unique to their input (else
it doesn't work), and can take multiple years to decode when it does work. A nice word for this
is *experimental*.
