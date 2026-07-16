import voice


def test_voice_module_exposes_speak():
    assert callable(voice.speak)
