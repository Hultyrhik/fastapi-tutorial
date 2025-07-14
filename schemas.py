from pydantic import BaseModel


class ItemCreateSchema(BaseModel):
    name: str
    description: str


class ItemUpdateSchema(BaseModel):
    name: str
    description: str
