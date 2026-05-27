import peewee as pw
from datetime import datetime, date
from .database import db

class BaseModel(pw.Model):
    class Meta:
        database = db

class Transaction(BaseModel):
    description = pw.CharField(index=True)
    amount = pw.FloatField()
    type = pw.CharField()  # "receita" ou "despesa"
    category = pw.CharField(index=True)
    date = pw.DateField(default=date.today())
    is_paid = pw.BooleanField(default=False)

    class Meta:
        table_name = "transactions"

class User(BaseModel):
    email = pw.CharField(unique=True, index=True)
    hashed_password = pw.CharField()
    is_active = pw.BooleanField(default=True)

    class Meta:
        table_name = "users"