from typing import Any

from app.services.genre_sentence import decade_of, genre_sentence


def movie(genres: list[str], year: int) -> dict[str, Any]:
    return {"genres": genres, "year": year}


def test_uses_the_two_most_common_genres_and_decade() -> None:
    picks = [
        movie(["Crime", "Drama"], 1994),
        movie(["Crime", "Thriller"], 1995),
        movie(["Crime", "Drama"], 1990),
        movie(["Action"], 1972),
    ]

    assert genre_sentence(picks) == "You gravitate toward Crime and Drama, especially films from the 1990s."


def test_ties_break_alphabetically_and_by_earliest_decade() -> None:
    picks = [movie(["Horror"], 1980), movie(["Comedy"], 1970), movie(["Animation"], 2000), movie(["Drama"], 2005)]

    # Every genre appears once -> first two alphabetically; 2000s has 2 picks, so it wins the decade.
    assert genre_sentence(picks) == "You gravitate toward Animation and Comedy, especially films from the 2000s."


def test_same_picks_in_any_order_give_the_same_sentence() -> None:
    picks = [movie(["Horror"], 1980), movie(["Comedy"], 1970), movie(["Drama"], 1960)]

    assert genre_sentence(picks) == genre_sentence(list(reversed(picks)))


def test_ignores_tags_that_are_not_genres() -> None:
    picks = [movie(["IMAX", "Sci-Fi"], 2010), movie(["IMAX", "Action"], 2012), movie(["IMAX", "Action"], 2014)]

    assert genre_sentence(picks) == "You gravitate toward Action and Sci-Fi, especially films from the 2010s."


def test_single_genre_picks_name_one_genre() -> None:
    picks = [movie(["Drama"], 1950), movie(["Drama"], 1957)]

    assert genre_sentence(picks) == "You gravitate toward Drama, especially films from the 1950s."


def test_picks_without_genres_still_get_a_sentence() -> None:
    assert genre_sentence([movie(["(no genres listed)"], 2001)]) == "You gravitate toward films from the 2000s."


def test_decade_of() -> None:
    assert decade_of(1999) == 1990
    assert decade_of(2000) == 2000
