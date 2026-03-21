from fastapi import FastAPI, HTTPException, Query, status
from pydantic import BaseModel, Field
from typing import Optional

app = FastAPI()

# =========================
# DATA (Day 1)
# =========================

movies = [
    {"id": 1, "title": "Avengers", "genre": "Action", "language": "English", "duration_mins": 150, "ticket_price": 300, "seats_available": 50},
    {"id": 2, "title": "KGF", "genre": "Action", "language": "Kannada", "duration_mins": 155, "ticket_price": 250, "seats_available": 40},
    {"id": 3, "title": "Interstellar", "genre": "Drama", "language": "English", "duration_mins": 170, "ticket_price": 350, "seats_available": 30},
    {"id": 4, "title": "Drishyam", "genre": "Drama", "language": "Hindi", "duration_mins": 140, "ticket_price": 200, "seats_available": 35},
    {"id": 5, "title": "Hangover", "genre": "Comedy", "language": "English", "duration_mins": 110, "ticket_price": 180, "seats_available": 25},
    {"id": 6, "title": "Conjuring", "genre": "Horror", "language": "English", "duration_mins": 120, "ticket_price": 220, "seats_available": 20}
]

bookings = []
booking_counter = 1

holds = []
hold_counter = 1

# =========================
# MODELS (Day 2)
# =========================

class BookingRequest(BaseModel):
    customer_name: str = Field(..., min_length=2)
    movie_id: int = Field(..., gt=0)
    seats: int = Field(..., gt=0, le=10)
    phone: str = Field(..., min_length=10)
    seat_type: str = "standard"
    promo_code: str = ""


class NewMovie(BaseModel):
    title: str = Field(..., min_length=2)
    genre: str = Field(..., min_length=2)
    language: str = Field(..., min_length=2)
    duration_mins: int = Field(..., gt=0)
    ticket_price: int = Field(..., gt=0)
    seats_available: int = Field(..., gt=0)


class SeatHoldRequest(BaseModel):
    customer_name: str
    movie_id: int
    seats: int


# =========================
# HELPERS (Day 3)
# =========================

def find_movie(movie_id):
    for m in movies:
        if m["id"] == movie_id:
            return m
    return None


def calculate_ticket_cost(price, seats, seat_type, promo_code):
    multiplier = 1
    if seat_type == "premium":
        multiplier = 1.5
    elif seat_type == "recliner":
        multiplier = 2

    original = price * seats * multiplier

    discount = 0
    if promo_code == "SAVE10":
        discount = 0.10
    elif promo_code == "SAVE20":
        discount = 0.20

    final = original * (1 - discount)

    return original, final


def filter_movies_logic(genre, language, max_price, min_seats):
    result = movies

    if genre is not None:
        result = [m for m in result if m["genre"].lower() == genre.lower()]

    if language is not None:
        result = [m for m in result if m["language"].lower() == language.lower()]

    if max_price is not None:
        result = [m for m in result if m["ticket_price"] <= max_price]

    if min_seats is not None:
        result = [m for m in result if m["seats_available"] >= min_seats]

    return result


# =========================
# DAY 1 (Q1–Q5)
# =========================

@app.get("/")
def home():
    return {"message": "Welcome to CineStar Booking"}


@app.get("/movies")
def get_movies():
    total_seats = sum(m["seats_available"] for m in movies)
    return {"movies": movies, "total": len(movies), "total_seats_available": total_seats}


@app.get("/movies/summary")
def summary():
    prices = [m["ticket_price"] for m in movies]
    total_seats = sum(m["seats_available"] for m in movies)

    genre_count = {}
    for m in movies:
        genre_count[m["genre"]] = genre_count.get(m["genre"], 0) + 1

    return {
        "total_movies": len(movies),
        "most_expensive": max(prices),
        "cheapest": min(prices),
        "total_seats": total_seats,
        "genre_count": genre_count
    }


@app.get("/bookings")
def get_bookings():
    total_revenue = sum(b["discounted_cost"] for b in bookings) if bookings else 0
    return {"bookings": bookings, "total": len(bookings), "total_revenue": total_revenue}


@app.get("/movies/filter")
def filter_movies(
    genre: Optional[str] = None,
    language: Optional[str] = None,
    max_price: Optional[int] = None,
    min_seats: Optional[int] = None
):
    return filter_movies_logic(genre, language, max_price, min_seats)


@app.get("/movies/search")
def search_movies(keyword: str):
    result = [
        m for m in movies
        if keyword.lower() in m["title"].lower()
        or keyword.lower() in m["genre"].lower()
        or keyword.lower() in m["language"].lower()
    ]

    if not result:
        return {"message": "No movies found"}

    return {"results": result, "total_found": len(result)}


@app.get("/movies/sort")
def sort_movies(sort_by: str = "ticket_price"):
    if sort_by not in ["ticket_price", "title", "duration_mins", "seats_available"]:
        raise HTTPException(status_code=400, detail="Invalid field")

    return sorted(movies, key=lambda x: x[sort_by])


@app.get("/movies/page")
def paginate(page: int = 1, limit: int = 3):
    start = (page - 1) * limit
    end = start + limit

    total_pages = (len(movies) + limit - 1) // limit

    return {"total": len(movies), "total_pages": total_pages, "data": movies[start:end]}


@app.get("/movies/browse")
def browse(
    keyword: Optional[str] = None,
    genre: Optional[str] = None,
    language: Optional[str] = None,
    sort_by: str = "ticket_price",
    order: str = "asc",
    page: int = 1,
    limit: int = 3
):
    result = movies

    if keyword:
        result = [m for m in result if keyword.lower() in m["title"].lower()]

    if genre:
        result = [m for m in result if m["genre"].lower() == genre.lower()]

    if language:
        result = [m for m in result if m["language"].lower() == language.lower()]

    result = sorted(result, key=lambda x: x[sort_by], reverse=(order == "desc"))

    start = (page - 1) * limit
    end = start + limit

    return {"total": len(result), "data": result[start:end]}


@app.get("/movies/{movie_id}")
def get_movie(movie_id: int):
    movie = find_movie(movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    return movie


# =========================
# DAY 2–3 (Q6–Q10)
# =========================

@app.post("/bookings")
def create_booking(data: BookingRequest):
    global booking_counter

    movie = find_movie(data.movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    if movie["seats_available"] < data.seats:
        raise HTTPException(status_code=400, detail="Not enough seats")

    original, final = calculate_ticket_cost(
        movie["ticket_price"], data.seats, data.seat_type, data.promo_code
    )

    movie["seats_available"] -= data.seats

    booking = {
        "booking_id": booking_counter,
        "customer_name": data.customer_name,
        "movie_title": movie["title"],
        "seats": data.seats,
        "seat_type": data.seat_type,
        "original_cost": original,
        "discounted_cost": final
    }

    bookings.append(booking)
    booking_counter += 1

    return booking


# =========================
# DAY 4 CRUD (Q11–Q13)
# =========================

@app.post("/movies", status_code=201)
def add_movie(new_movie: NewMovie):
    for m in movies:
        if m["title"].lower() == new_movie.title.lower():
            raise HTTPException(status_code=400, detail="Duplicate movie")

    movie = new_movie.dict()
    movie["id"] = len(movies) + 1
    movies.append(movie)

    return movie


@app.put("/movies/{movie_id}")
def update_movie(movie_id: int, ticket_price: Optional[int] = None, seats_available: Optional[int] = None):
    movie = find_movie(movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    if ticket_price is not None:
        movie["ticket_price"] = ticket_price

    if seats_available is not None:
        movie["seats_available"] = seats_available

    return movie


@app.delete("/movies/{movie_id}")
def delete_movie(movie_id: int):
    movie = find_movie(movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    for b in bookings:
        if b["movie_title"] == movie["title"]:
            raise HTTPException(status_code=400, detail="Cannot delete, bookings exist")

    movies.remove(movie)
    return {"message": "Movie deleted"}


# =========================
# DAY 5 WORKFLOW (Q14–Q15)
# =========================

@app.post("/seat-hold")
def hold_seat(data: SeatHoldRequest):
    global hold_counter

    movie = find_movie(data.movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    if movie["seats_available"] < data.seats:
        raise HTTPException(status_code=400, detail="Not enough seats")

    movie["seats_available"] -= data.seats

    hold = {
        "hold_id": hold_counter,
        "customer_name": data.customer_name,
        "movie_id": data.movie_id,
        "seats": data.seats
    }

    holds.append(hold)
    hold_counter += 1

    return hold


@app.get("/seat-hold")
def get_holds():
    return holds


@app.post("/seat-confirm/{hold_id}")
def confirm_hold(hold_id: int):
    global booking_counter

    hold = next((h for h in holds if h["hold_id"] == hold_id), None)
    if not hold:
        raise HTTPException(status_code=404, detail="Hold not found")

    movie = find_movie(hold["movie_id"])

    booking = {
        "booking_id": booking_counter,
        "customer_name": hold["customer_name"],
        "movie_title": movie["title"],
        "seats": hold["seats"],
        "discounted_cost": hold["seats"] * movie["ticket_price"]
    }

    bookings.append(booking)
    holds.remove(hold)
    booking_counter += 1

    return booking


@app.delete("/seat-release/{hold_id}")
def release_hold(hold_id: int):
    hold = next((h for h in holds if h["hold_id"] == hold_id), None)
    if not hold:
        raise HTTPException(status_code=404, detail="Hold not found")

    movie = find_movie(hold["movie_id"])
    movie["seats_available"] += hold["seats"]

    holds.remove(hold)

    return {"message": "Hold released"}


# =========================
# DAY 6 BOOKINGS SEARCH (Q19)
# =========================

@app.get("/bookings/search")
def search_bookings(name: str):
    return [b for b in bookings if name.lower() in b["customer_name"].lower()]


@app.get("/bookings/sort")
def sort_bookings(sort_by: str = "discounted_cost"):
    if sort_by not in ["discounted_cost", "seats"]:
        raise HTTPException(status_code=400, detail="Invalid field")

    return sorted(bookings, key=lambda x: x[sort_by])


@app.get("/bookings/page")
def paginate_bookings(page: int = 1, limit: int = 3):
    start = (page - 1) * limit
    end = start + limit

    total_pages = (len(bookings) + limit - 1) // limit

    return {"total": len(bookings), "total_pages": total_pages, "data": bookings[start:end]}
