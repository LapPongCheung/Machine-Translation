from wtforms.form import Form
from wtforms.fields import FieldList, FormField, IntegerField, BooleanField, StringField, TextField, TextAreaField

class Row(Form):
	chinese = TextAreaField('')

class Table(Form):
	rows = FieldList(FormField(Row))
