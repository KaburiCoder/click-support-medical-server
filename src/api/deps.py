from typing import Annotated
from fastapi import Depends
from src.core.db import AsyncSession, get_db

SessionDep = Annotated[AsyncSession, Depends(get_db)]


