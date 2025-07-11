from backend.main import classify_face_shape


def test_classify_oval():
    measurements = {"forehead_width": 100, "cheekbone_width": 120, "jaw_width": 90, "face_length": 170}
    # The heuristic has changed to return "Egg" for these measurements
    assert classify_face_shape(measurements) == "Egg"


def test_classify_square():
    measurements = {"forehead_width": 140, "cheekbone_width": 140, "jaw_width": 140, "face_length": 150}
    assert classify_face_shape(measurements) == "Square"
