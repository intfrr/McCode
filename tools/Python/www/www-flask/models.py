from app import db, ModelBase
from json import dumps, loads
from datetime import datetime

class User(ModelBase):
    ''' A user of the system '''
    __tablename__ = 'user'
    username = db.Column(db.String(64), primary_key=True)
    passhash = db.Column(db.String(128), primary_key=True)


class Job(ModelBase):
    ''' A job specifying the simuation to run and its status '''
    __tablename__ = 'job'
    id      = db.Column(db.String(38), primary_key=True)
    seed    = db.Column(db.Integer)
    samples = db.Column(db.Integer)
    npoints = db.Column(db.Integer)
    sim_id  = db.Column(db.Integer, db.ForeignKey('simulation.id'))
    params  = db.relationship('ParamValue', backref='job', lazy=False)
    created = db.Column(db.DateTime(timezone=False), index=True)

    def __init__(self, id, seed, samples, npoints, sim):
        self.id = id
        self.seed = seed
        self.samples = samples
        self.npoints = npoints
        self.sim_id = sim.id
        self.created = datetime.now()


class Simulation(ModelBase):
    ''' A simulation '''
    __tablename__ = 'simulation'
    id     = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name   = db.Column(db.String(64))
    params = db.relationship('Param', backref='sim', lazy=False, order_by='Param.priority')
    jobs   = db.relationship('Job', backref='sim')
    runs   = db.relationship('SimRun', backref='sim')

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return self.name


class SimRun(ModelBase):
    ''' A particular run of a simulation (configured by Job) '''
    __tablename__ = 'sim_run'
    id     = db.Column(db.String(64), primary_key=True)
    job_id = db.Column(db.String(38), db.ForeignKey('job.id'))
    sim_id = db.Column(db.Integer, db.ForeignKey('simulation.id'))
    user   = db.Column(db.Integer, db.ForeignKey('user.username'))

    status = db.Column(db.String(32), index=True)
    str_params = db.Column(db.String())
    str_result = db.Column(db.String())
    created = db.Column(db.DateTime(timezone=False), index=True)
    completed = db.Column(db.DateTime(timezone=False), index=True)

    def __init__(self, user, job, sim, params):
        self.id     = job.id + "__" + str(datetime.now()).replace(' ', '_')
        self.user   = user
        self.job_id = job.id
        self.sim_id = sim.id
        self.status = "waiting"
        self.params = params
        self.result = ""
        self.created = datetime.now()
        self.completed = None

    @property
    def params(self):
        return loads(self.str_params)
    @params.setter
    def params(self, p):
        self.str_params = dumps(p)

    @property
    def result(self):
        return loads(self.str_result)
    @result.setter
    def result(self, r):
        self.str_result = dumps(r)


class Param(ModelBase):
    ''' A parameter '''
    __tablename__ = 'param'
    id = db.Column(db.Integer, primary_key=True)

    priority = db.Column(db.Integer)

    name = db.Column(db.String(127))
    unit = db.Column(db.String(127))
    msg  = db.Column(db.String(127))

    str_default = db.Column(db.String(255))

    sim_id = db.Column(db.ForeignKey('simulation.id'))

    values   = db.relationship('ParamValue', backref='param', lazy=False)

    def __init__(self, sim, name):
        self.sim_id = sim.id
        self.name = name

    def simulation(self):
        return Simulation.query.filter_by(id=self.sim_id).one()

    @property
    def default_value(self):
        return loads(self.str_default)
    @default_value.setter
    def default_value(self, val):
        self.str_default = dumps(val)


class ParamValue(ModelBase):
    ''' A parameter value tied to a specific job '''
    __tablename__ = 'param_value'
    id        = db.Column(db.Integer, primary_key=True)
    param_id  = db.Column(db.Integer, db.ForeignKey('param.id'))
    str_value = db.Column(db.PickleType)
    job_id    = db.Column(db.ForeignKey('job.id'))

    def __init__(self, param, value, job):
        self.param_id = param.id
        self.value    = value
        self.job_id   = job.id

    @property
    def value(self):
        return loads(self.str_value)
    @value.setter
    def value(self, val):
        self.str_value = dumps(val)
