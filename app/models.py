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
    is_superuser = pw.BooleanField(default=False)
    modules = pw.TextField(default='["finance","lists"]')

    class Meta:
        table_name = "users"

class ShoppingList(BaseModel):
    owner = pw.ForeignKeyField(User, backref='lists')
    title = pw.CharField()
    description = pw.TextField(null=True)
    type = pw.CharField()  # 'shopping', 'todo', 'bullet'
    icon = pw.CharField(max_length=50, null=True)
    status = pw.CharField(default='active')  # active, archived, deleted
    position = pw.IntegerField(default=0)
    created_at = pw.DateTimeField(default=datetime.now)
    updated_at = pw.DateTimeField(default=datetime.now)
    deleted_at = pw.DateTimeField(null=True)

    class Meta:
        table_name = 'shopping_lists'

class ListItem(BaseModel):
    list = pw.ForeignKeyField(ShoppingList, backref='items')
    text = pw.CharField()
    is_completed = pw.BooleanField(default=False)
    position = pw.IntegerField(default=0)
    priority = pw.CharField(max_length=10, null=True)  # low, medium, high
    due_date = pw.DateField(null=True)
    quantity = pw.FloatField(null=True)
    unit = pw.CharField(max_length=20, null=True)
    category = pw.CharField(max_length=50, null=True)
    price = pw.FloatField(null=True)
    created_by = pw.ForeignKeyField(User, null=True)
    created_at = pw.DateTimeField(default=datetime.now)
    updated_at = pw.DateTimeField(default=datetime.now)

    class Meta:
        table_name = 'list_items'
