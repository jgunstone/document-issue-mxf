from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


# class FunctionalBreakdown(Base):
#     """i.e. volume, high-level workpackage..."""
#     ...

# class SpatialBreakdown(Base):
#     """i.e. volume, level..."""
#     ...

# class Level(Base):
#     id = Column(Integer, primary_key=True, index=True)
#     code = Column(String)
#     description = Column(String)

# class Discipline(Base):
#     """technical branch of industry"""
#     id = Column(Integer, primary_key=True, index=True)
#     code = Column(String)
#     description = Column(String, unique=True)

# class Form(Base):
#     """information type"""
#     id = Column(Integer, primary_key=True, index=True)
#     code = Column(String)
#     description = Column(String)
#     version = Column(Integer)

# class ProjectForm(Base):
#     """forms in use on project"""
#     form_id = Column(Integer, ForeignKey("form.id"), primary_key=True)
#     project_id = Column(Integer, ForeignKey("project.id"), primary_key=True)
#     code = Column(String)  # override code...

# class Nomenclature(Base):
#     id = Column(Integer, primary_key=True, index=True)
#     nomenclature = Column(String)
#     # e.g. "{project_code}-{originator}-{volume}-{level}-{form[0]}-{discipline[0]}-{discipline[1]}{form[1]}{sequence}"

# class ProjectNomenclature(Base):
#     nomenclature_id = Column(Integer, ForeignKey("nomenclature.id"), primary_key=True)
#     project_id = Column(Integer, ForeignKey("project.id"), primary_key=True)
#     nomenclature = Column(String)  # override code...

# class ProjectSetup(Base):
#     id = Column(Integer, primary_key=True, index=True)  # can just use the project key?
#     project_id = Column(Integer, ForeignKey("project.id"), primary_key=True)
#     no_levels = Column(Integer)
#     no_volumes = Column(Integer)
#     no_sheets = Column(Integer)


# -----------------
# below for future stuff


class BaseCode:
    code = Column(String)
    description = Column(String)


class Nomenclature(Base):
    # __versioned__ = {}
    __tablename__ = "nomemclature"

    id = Column(Integer, primary_key=True, index=True)
    definition = Column(JSON)


# class Project(Base) # see below
#    ...


class Originator(BaseCode, Base):
    """Stores the originator of a document."""

    # __versioned__ = {}
    __tablename__ = "originator"

    id = Column(Integer, primary_key=True, index=True)


class ProjectOriginator(Base):  # allows project to override the codes
    __tablename__ = "project_originator"

    project_id = Column(Integer, ForeignKey("project.id"), primary_key=True)
    originator_id = Column(Integer, ForeignKey("originator.id"), primary_key=True)
    code = Column(String)

    UniqueConstraint(project_id, originator_id)


class Level(BaseCode, Base):
    """Stores the level of a document."""

    # __versioned__ = {}
    __tablename__ = "level"

    id = Column(Integer, primary_key=True, index=True)


class ProjectLevel(Base):  # allows project to override the codes
    __tablename__ = "project_level"

    project_id = Column(Integer, ForeignKey("project.id"), primary_key=True)
    level_id = Column(Integer, ForeignKey("level.id"), primary_key=True)
    code = Column(String)

    UniqueConstraint(project_id, level_id)


class Classification(BaseCode, Base):  # Discipline
    """Stores the classification of a document."""

    # __versioned__ = {}
    __tablename__ = "classification"

    id = Column(Integer, primary_key=True, index=True)


class ProjectClassification(Base):  # allows project to override the codes
    __tablename__ = "project_classification"

    project_id = Column(Integer, ForeignKey("project.id"), primary_key=True)
    classification_id = Column(Integer, ForeignKey("classification.id"), primary_key=True)
    code = Column(String)

    UniqueConstraint(project_id, classification_id)


class InformationType(BaseCode, Base):  # Form
    """Stores the information type of a document."""

    # __versioned__ = {}
    __tablename__ = "information_type"

    id = Column(Integer, primary_key=True, index=True)


class ProjectInformationType(Base):  # Form
    """Stores the information type of a document."""

    # __versioned__ = {}
    __tablename__ = "project_information_type"

    id = Column(Integer, primary_key=True, index=True)

    project_id = Column(Integer, ForeignKey("project.id"), primary_key=True)
    information_type_id = Column(Integer, ForeignKey("information_type.id"), primary_key=True)
    code = Column(String)

    UniqueConstraint(project_id, information_type_id)


class DocumentCodeGenerator(Base):
    """Stores the code generation of a document. This the practice default."""

    # __versioned__ = {}
    __tablename__ = "document_code_generator"

    id = Column(Integer, primary_key=True, index=True)
    version = Column(Integer)
    issue_date = Column(Date)
    map_classification = Column(JSON)
    map_information_type = Column(JSON)
    map_level = Column(JSON)
    map_originator = Column(JSON)


class ProjectDocumentCodeGenerator(Base):
    """Stores the code generation of a document for a project. This is the project override"""

    # __versioned__ = {}
    __tablename__ = "project_document_code_generator"

    id = Column(Integer, primary_key=True, index=True)
    map_classification = Column(JSON)  # , allow_null=True)
    map_information_type = Column(JSON)  # , allow_null=True)
    map_level = Column(JSON)  # , allow_null=True)
    map_project = Column(JSON)
    map_originator = Column(JSON)

    document_code_generator_id = Column(Integer, ForeignKey("document_code_generator.id"))


# - ^^^ classification fields ^^^ ----------------------------------------


class Person(Base):
    """Stores the person's initials and full name."""

    # TODO: should this just store ID from WebApp?

    # __versioned__ = {}
    __tablename__ = "person"

    id = Column(Integer, primary_key=True, index=True)
    initials = Column(String)
    full_name = Column(String)

    # project_person = relationship("ProjectRole", back_populates="people")

    project_role = relationship("ProjectRole", back_populates="person", passive_deletes="all")
    UniqueConstraint(initials)


class Role(Base):
    """Stores the role of a person on a project."""

    # __versioned__ = {}
    __tablename__ = "role"

    id = Column(Integer, primary_key=True, index=True)
    role_name = Column(String)
    role_description = Column(String)
    is_archived = Column(Boolean, default=False)  # use if a role is no longer required but already in use historically.

    document_role = relationship("DocumentRole", back_populates="role", passive_deletes="all")
    project_role = relationship("ProjectRole", back_populates="role", passive_deletes="all")
    UniqueConstraint(role_name)


class ProjectRole(Base):
    __tablename__ = "project_role"
    project_id = Column(Integer, ForeignKey("project.id"), primary_key=True)
    role_id = Column(Integer, ForeignKey("role.id"), primary_key=True)
    person_id = Column(Integer, ForeignKey("person.id"))

    role = relationship("Role", back_populates="project_role")
    project = relationship("Project", back_populates="project_role")
    person = relationship("Person", back_populates="project_role")

    UniqueConstraint(project_id, role_id)


class Project(Base):
    """Stores the project/job number."""

    # __versioned__ = {}
    __tablename__ = "project"

    id = Column(Integer, primary_key=True, index=True)
    project_number = Column(Integer)
    project_code = Column(String)  # external facing code...
    project_name = Column(String)  #  remove / get from webapp
    project_address = Column(String)
    client_name = Column(String)

    project_role = relationship("ProjectRole", back_populates="project", cascade="all, delete-orphan")
    document = relationship("Document", back_populates="project", cascade="all, delete-orphan")
    UniqueConstraint(project_number)


class Issue(Base):
    """Stores the issue number."""

    # __versioned__ = {}
    __tablename__ = "issue"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("document.id"))

    revision_number = Column(Integer)
    revision = Column(String)
    date = Column(Date)
    # status = Column(String)  # maps to status code...
    status_revision = Column(String)
    status_code = Column(String)
    status_description = Column(String)
    author = Column(String)  # must be in project
    checked_by = Column(String)
    issue_format = Column(String)
    issue_notes = Column(String)

    document = relationship("Document", back_populates="issue")


class DocumentRole(Base):
    __tablename__ = "document_role"

    document_id = Column(Integer, ForeignKey("document.id"), primary_key=True)
    role_id = Column(Integer, ForeignKey("role.id"), primary_key=True)  # TODO: map to project role

    role = relationship("Role", back_populates="document_role")
    document = relationship("Document", back_populates="document_role")
    UniqueConstraint(document_id, role_id)


class Document(Base):
    """Stores the document number."""

    # __versioned__ = {}
    __tablename__ = "document"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("project.id"), nullable=False)

    name_nomenclature = Column(String)
    document_code = Column(String, nullable=False)
    document_description = Column(String)
    document_type = Column(String, nullable=False)
    document_source = Column(String)
    paper_size = Column(String)
    scale = Column(String)
    notes = Column(JSON)
    originator = Column(String)
    date_string_format = Column(String, nullable=False)
    output_author = Column(Boolean, nullable=False)
    output_checked_by = Column(Boolean, nullable=False)

    # is_archived = Column(Boolean, default=False) # TODO: add for document issued but no longer required

    document_role = relationship("DocumentRole", back_populates="document", cascade="all, delete-orphan")
    issue = relationship(
        "Issue",
        back_populates="document",
        cascade="all, delete, delete-orphan",
    )
    project = relationship("Project", back_populates="document")
    UniqueConstraint(project_id, document_code)  # i.e. unique within project


# -
