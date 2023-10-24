from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel,Field, create_engine, Session, select

"""
Using SQLModel to create a database model. The database will be used to store images and their captions.
The major goal of having a database is to be able to retrieve the image id of an image that has been uploaded to WhatsApp.
This make the chatbot able send images that were already created as the process of creating images is time consuming.
"""

engine=create_engine("sqlite:///./Database/database.sqlite3")

class Data(SQLModel):

    id:Optional[int]=Field(default=None,primary_key=True)
    name:str=Field(...,index=True,unique=True)
    image_id:int
    message:str
    caption:str
    file_path:str
    uploaded_at:datetime

    def save(self):
        with Session(engine) as session:
            session.add(self)
            session.commit()
            session.refresh(self)
        return self

    def update_image_id(self):
        with Session(engine) as session:
            data=session.exec(select(Data).where(Data.id==self.id)).one()
            if data:
                data.image_id=self.image_id
                session.add(data)
                session.commit()
                return data
            return None
  

    @classmethod
    def by_name(cls,name:str):
        try:
            with Session(engine) as session:
                return session.exec(select(cls).where(cls.name==name)).one()
        except:
            return None
        
    # get all data
    @classmethod
    def all(cls):
        with Session(engine) as session:
            return session.exec(select(cls)).all()
        
  

# My tables
class Performance(Data,SQLModel,table=True):
  pass

class Comparison(Data,SQLModel,table=True):
  pass

SQLModel.metadata.create_all(engine)