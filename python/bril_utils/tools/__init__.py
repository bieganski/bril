from typing import Generator, Sequence

def fresh(
    existing: Sequence[str] = [],
    prefix: str = "",
    use_letters_not_numbers: bool = False,
    ) -> Generator[str, None, None]:
    """
    @param 'existing' is not updated (up to caller to do so).
    """
    
    # use set for efficient lookup/add.
    existing_set = set(existing)

    from string import ascii_lowercase, digits
    sequence = ascii_lowercase if use_letters_not_numbers else digits

    # produces: "a", "b", ..., "aa", "ab", ...
    def _fresh_generator(sequence: Sequence, prefix: str):
        
        import itertools
    
        for i in itertools.count(1):
            for symbol in itertools.product(sequence, repeat=i):
                yield prefix + ''.join(symbol)
    
    gen = _fresh_generator(sequence=sequence, prefix=prefix)
    
    while True:
        new = yield from gen
        if new not in existing_set:
            existing_set.add(new)
            yield new
