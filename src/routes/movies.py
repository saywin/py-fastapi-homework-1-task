from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db, MovieModel
from schemas import MovieListResponseSchema, MovieDetailResponseSchema

router = APIRouter()


@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_movies_list(
        request: Request,
        page: int = Query(ge=1, default=1),
        per_page: int = Query(ge=1, le=20, default=10),
        db: AsyncSession = Depends(get_db)
):
    items = select(MovieModel).offset(page - 1).limit(per_page)
    count_items = select(func.count()).select_from(MovieModel)
    total_items = await db.scalar(count_items)
    result = await db.execute(items)
    movies = result.scalars().all()
    total_pages = total_items // per_page
    url_path = request.url.path

    if total_items == 0 or page > total_pages:
        raise HTTPException(status_code=404, detail="No movies found.")

    prev_page = f"{url_path}?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page = f"{url_path}?page={page + 1}&per_page={per_page}" if page <= total_pages else None

    return {
        "movies": movies,
        "prev_page": prev_page,
        "next_page": next_page,
        "total_items": total_items,
        "total_pages": total_pages,
    }


@router.get("/movies/{movie_id}/", response_model=MovieDetailResponseSchema)
async def get_movie_by_id(movie_id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(MovieModel).where(MovieModel.id == movie_id)
    result = await db.execute(stmt)
    movie = result.scalars().first()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    return movie
