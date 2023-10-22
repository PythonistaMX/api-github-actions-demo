from apiflask import APIBlueprint, abort
from marshmallow.exceptions import ValidationError

from apiflaskdemo.project.auth import login_required
from apiflaskdemo.project.models import Alumno, db
from apiflaskdemo.project.schemas import AlumnoInSchema, AlumnoSchema

abc_alumnos = APIBlueprint('abc_alumno', __name__)

@abc_alumnos.get("/alumnos/")
@abc_alumnos.output(AlumnoSchema(many=True))
def vuelca_base():
    # Método para volcar la base de datos
    return Alumno.query.all()

@abc_alumnos.get("/alumno/<int:cuenta>")
@abc_alumnos.output(AlumnoSchema)
def despliega_alumno(cuenta):
    '''Método para desplegar un alumno en particular'''
    return Alumno.query.get_or_404(cuenta)

@abc_alumnos.delete("/alumno/<int:cuenta>")
@abc_alumnos.output(AlumnoSchema)
@login_required
def elimina_alumno(cuenta):
    '''Método para eliminar un alumno en particular'''
    alumno = Alumno.query.get_or_404(cuenta)
    db.session.delete(alumno)
    db.session.commit()
    return alumno
    
@abc_alumnos.post("/alumno/<int:cuenta>")
@abc_alumnos.output(AlumnoSchema, status_code=201)
@abc_alumnos.input(AlumnoInSchema)
def crea_alumno(cuenta, data):
    '''Método para crear un alumno en particular'''
    if Alumno.query.filter_by(cuenta=cuenta).first():
        abort(409)
    else:
        data["cuenta"] = cuenta
        alumno = Alumno(**AlumnoSchema().load(data))
        db.session.add(alumno)
        db.session.commit()
        return alumno, 201

@abc_alumnos.put("/alumno/<int:cuenta>")
@abc_alumnos.output(AlumnoSchema)
@abc_alumnos.input(AlumnoInSchema)
def sustituye_alumno(cuenta, data):
    alumno = Alumno.query.get_or_404(cuenta)
    db.session.delete(alumno)
    data["cuenta"] = cuenta
    nuevo_alumno = Alumno(**data)
    db.session.add(nuevo_alumno)
    db.session.commit()
    return  nuevo_alumno