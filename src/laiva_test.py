import laiva

def test_allowed_channel():
    assert laiva.is_allowed_channel(359308335184609281)
    assert not laiva.is_allowed_channel(563272263399374850)
