from webapp.controllers.misc import trim_non_alpha


def test_trim_non_alpha():
    assert trim_non_alpha("a") == "a"
    assert trim_non_alpha(".a") == "a"
    assert trim_non_alpha("a.") == "a"
