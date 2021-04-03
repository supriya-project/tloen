import pytest

from tloen.domain import Clip, Note, NoteMoment


@pytest.mark.parametrize(
    "inputs, expected",
    [
        (
            (False, 0, 1, 0, 1, 0, 1, [Note(0, 1)]),
            {
                (0.0, 0.0, False): NoteMoment(
                    offset=0.0, next_offset=1.0, start_notes=[Note(0, 1)]
                ),
                (0.5, 0.0, False): NoteMoment(
                    offset=0.5, next_offset=1.0, overlap_notes=[Note(0, 1)]
                ),
                (0.5, 0.0, True): NoteMoment(offset=0.5, stop_notes=[Note(0, 1)]),
                (1.0, 0.0, False): NoteMoment(offset=1.0, stop_notes=[Note(0, 1)]),
                (1.5, 0.0, False): NoteMoment(offset=1.5),
            },
        ),
        (
            (False, 0, 1, 0, 1, 0, 1, [Note(0.25, 0.75)]),
            {
                (0.0, 0.0, False): NoteMoment(offset=0.0, next_offset=0.25),
                (0.25, 0.0, False): NoteMoment(
                    offset=0.25, next_offset=0.75, start_notes=[Note(0.25, 0.75)]
                ),
                (0.5, 0.0, False): NoteMoment(
                    offset=0.5, next_offset=0.75, overlap_notes=[Note(0.25, 0.75)]
                ),
                (0.5, 0.0, True): NoteMoment(offset=0.5, stop_notes=[Note(0.25, 0.75)]),
                (0.75, 0.0, False): NoteMoment(
                    offset=0.75, next_offset=1.0, stop_notes=[Note(0.25, 0.75)]
                ),
                (1.0, 0.0, False): NoteMoment(offset=1.0),
                (1.5, 0.0, False): NoteMoment(offset=1.5),
            },
        ),
        (
            (False, 0, 1, -1, 1, 0, 1, [Note(0, 1)]),
            {
                (0.0, 0.0, False): NoteMoment(offset=0.0, next_offset=1.0),
                (1.0, 0.0, False): NoteMoment(
                    offset=1.0, next_offset=2.0, start_notes=[Note(0, 1)]
                ),
                (1.5, 0.0, False): NoteMoment(
                    offset=1.5, next_offset=2.0, overlap_notes=[Note(0, 1)]
                ),
                (1.5, 0.0, True): NoteMoment(offset=1.5, stop_notes=[Note(0, 1)]),
                (2.0, 0.0, False): NoteMoment(offset=2.0, stop_notes=[Note(0, 1)]),
                (2.5, 0.0, False): NoteMoment(offset=2.5),
            },
        ),
        (
            (True, 0, 1, 0, 1, 0, 1, [Note(0, 1)]),
            {
                (0.0, 0.0, False): NoteMoment(
                    offset=0.0, next_offset=1.0, start_notes=[Note(0, 1)]
                ),
                (0.5, 0.0, False): NoteMoment(
                    offset=0.5, next_offset=1.0, overlap_notes=[Note(0, 1)]
                ),
                (1.0, 0.0, False): NoteMoment(
                    offset=1.0,
                    next_offset=2.0,
                    start_notes=[Note(0, 1)],
                    stop_notes=[Note(0, 1)],
                ),
                (2.0, 0.0, False): NoteMoment(
                    offset=2.0,
                    next_offset=3.0,
                    start_notes=[Note(0, 1)],
                    stop_notes=[Note(0, 1)],
                ),
            },
        ),
        (
            (True, 0, 1, 0, 1, 0, 1, [Note(0.25, 0.75)]),
            {
                (0.0, 0.0, False): NoteMoment(offset=0.0, next_offset=0.25),
                (0.25, 0.0, False): NoteMoment(
                    offset=0.25, next_offset=0.75, start_notes=[Note(0.25, 0.75)]
                ),
                (0.5, 0.0, False): NoteMoment(
                    offset=0.5, next_offset=0.75, overlap_notes=[Note(0.25, 0.75)]
                ),
                (0.5, 0.0, True): NoteMoment(offset=0.5, stop_notes=[Note(0.25, 0.75)]),
                (0.75, 0.0, False): NoteMoment(
                    offset=0.75, next_offset=1.0, stop_notes=[Note(0.25, 0.75)]
                ),
                (1.0, 0.0, False): NoteMoment(offset=1.0, next_offset=1.25),
                (1.25, 0.0, False): NoteMoment(
                    offset=1.25, next_offset=1.75, start_notes=[Note(0.25, 0.75)]
                ),
            },
        ),
        (
            (True, 0, 1, -1, 1, 0, 1, [Note(0, 1)]),
            {
                (-1.0, 0.0, False): NoteMoment(offset=-1.0, next_offset=1.0),
                (0.0, 0.0, False): NoteMoment(offset=0.0, next_offset=1.0),
                (1.0, 0.0, False): NoteMoment(
                    offset=1.0, next_offset=2.0, start_notes=[Note(0, 1)]
                ),
                (1.5, 0.0, False): NoteMoment(
                    offset=1.5, next_offset=2.0, overlap_notes=[Note(0, 1)]
                ),
                (2.0, 0.0, False): NoteMoment(
                    offset=2.0,
                    next_offset=3.0,
                    start_notes=[Note(0, 1)],
                    stop_notes=[Note(0, 1)],
                ),
                (3.0, 0.0, False): NoteMoment(
                    offset=3.0,
                    next_offset=4.0,
                    start_notes=[Note(0, 1)],
                    stop_notes=[Note(0, 1)],
                ),
            },
        ),
        (
            (True, 0, 1, -1, 1, 0, 1, [Note(0.25, 0.75)]),
            {(0.0, 0.0, False): NoteMoment(offset=0.0, next_offset=1.25),},
        ),
        (
            (True, 0, 1, 0.5, 1, 0, 1, [Note(0.25, 0.75)]),
            {
                (0.0, 0.0, False): NoteMoment(
                    offset=0.0, next_offset=0.25, overlap_notes=[Note(0.25, 0.75)]
                ),
            },
        ),
    ],
)
def test_at(
    inputs, expected,
):
    (
        is_looping,
        loop_start_marker,
        loop_stop_marker,
        start_marker,
        stop_marker,
        start_offset,
        stop_offset,
        notes,
    ) = inputs
    if isinstance(expected, Exception):
        with pytest.raises(expected):
            clip = Clip(
                is_looping=is_looping,
                loop_start_marker=loop_start_marker,
                loop_stop_marker=loop_stop_marker,
                start_marker=start_marker,
                start_offset=start_offset,
                stop_marker=stop_marker,
                stop_offset=stop_offset,
                notes=notes,
            )
    else:
        clip = Clip(
            is_looping=is_looping,
            loop_start_marker=loop_start_marker,
            loop_stop_marker=loop_stop_marker,
            start_marker=start_marker,
            start_offset=start_offset,
            stop_marker=stop_marker,
            stop_offset=stop_offset,
            notes=notes,
        )
        actual = {}
        for (offset, start_delta, force_stop), moment in expected.items():
            actual[(offset, start_delta, force_stop)] = clip.at(
                offset, start_delta=start_delta, force_stop=force_stop
            )
        assert actual == expected
