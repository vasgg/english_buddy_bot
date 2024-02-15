from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import delete, select

from bot.resources.enums import ReactionType
from database.db import AsyncDBSession

from database.models.reaction import Reaction

reactions_router = APIRouter()
templates = Jinja2Templates(directory='src/webapp/templates')


@reactions_router.get("/reactions", response_class=HTMLResponse)
async def read_answers(request: Request, db_session: AsyncDBSession):
    result = await db_session.execute(select(Reaction))
    data = result.scalars().all()
    right = [reaction for reaction in data if reaction.type.value == 'right']
    wrong = [reaction for reaction in data if reaction.type.value == 'wrong']
    return templates.TemplateResponse(request=request, name="reactions.html", context={'right': right, 'wrong': wrong})


@reactions_router.post("/reactions")
async def save_reactions(request: Request, db_session: AsyncDBSession):
    form_data = await request.form()
    reactions_to_update = []
    new_reactions = []
    for key, value in form_data.items():
        if '_new' in key:
            reaction_type = key.replace("_new", "").lower().split("_")[0]
            new_reaction = Reaction(text=value, type=ReactionType(reaction_type))
            db_session.add(new_reaction)
        else:
            reaction_id = int(key.split("_")[1])
            reaction_type = key.split("_")[0]
            query = await db_session.execute(select(Reaction).filter(Reaction.id == reaction_id))
            reaction = query.scalar_one_or_none()

            if reaction:
                reaction.text = value
                reaction.type = ReactionType(reaction_type)
                reactions_to_update.append(reaction)
            else:
                raise HTTPException(status_code=404, detail=f"Reaction with id {reaction_id} not found")

    db_session.add_all(reactions_to_update)

    for new_reaction in new_reactions:
        db_reaction = Reaction(text=new_reaction.text, type=new_reaction.type)
        db_session.add(db_reaction)

    return {"message": "Reactions saved successfully"}


@reactions_router.delete("/reactions/{reaction_id}")
async def delete_reaction(reaction_id: int, db_session: AsyncDBSession):
    reaction = await db_session.execute(select(Reaction).filter(Reaction.id == reaction_id))
    reaction = reaction.scalar_one_or_none()
    if not reaction:
        raise HTTPException(status_code=404, detail="Reaction not found")
    query = delete(Reaction).filter(Reaction.id == reaction_id)
    await db_session.execute(query)
    await db_session.commit()
    return {"message": "Reaction deleted successfully"}
