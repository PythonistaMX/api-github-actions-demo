from apiflask import Schema
from apiflask.fields import Boolean, Float, Integer, String
from apiflask.validators import Length, OneOf, Range

carreras = ("Sistemas", "Derecho", "Actuaría", "Arquitectura", "Administración")
variable = None

class AlumnoSchema(Schema):
    cuenta = Integer(required=True, validate=Range(min=1000000, max=9999999))
    nombre = String(required=True, validate=Length(min=2, max=50))
    primer_apellido = String(required=True, validate=Length(min=2, max=50))
    segundo_apellido = String(required=False, validate=Length(min=2, max=50))
    carrera = String(required=True, validate=OneOf(carreras))
    semestre = Integer(required=True, validate=Range(min=1, max=50))
    promedio = Float(required=True, validate=Range(min=1, max=10))
    al_corriente = Boolean(required=True)

class AlumnoInSchema(Schema):
    nombre = String(required=True, validate=Length(min=2, max=50))
    primer_apellido = String(required=True, validate=Length(min=2, max=50))
    segundo_apellido = String(required=False, validate=Length(min=2, max=50))
    carrera = String(required=True, validate=OneOf(carreras))
    semestre = Integer(required=True, validate=Range(min=1, max=50))
    promedio = Float(required=True, validate=Range(min=0, max=10))
    al_corriente = Boolean(required=True)