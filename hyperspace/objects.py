import json
from datetime import datetime
from dataclasses import dataclass, asdict, make_dataclass
import random

from hyperspace.utilities import sanitize_email, timestamp
from hyperspace.murd import mddb, murd


def BuildStamp(stampName):
    def dataClassBuilder(dataClass):

        def stampNamer(stamp_name):
            return f"{stamp_name.capitalize()}Stamp"

        stampFieldName = stampNamer(stampName)

        stampDataClass = make_dataclass(
            stampName,
            fields=[(stampFieldName, str, None)],
            namespace={
                f"stamp{stampName.upper()}": lambda self: setattr(self, stampFieldName, timestamp()),
                f"timeSince{stampName.upper()}":
                    lambda self:
                        None
                        if not (stamp := getattr(self, stampFieldName)) else
                        (datetime.utcnow() - datetime.fromisoformat(stamp)).total_seconds(),
                "get_stamp": lambda self, stamp_name: getattr(self, stampNamer(stamp_name), None),
                "time_since": lambda self, stamp_name: getattr(self, f"timeSince{stamp_name.upper()}", lambda: None)()
            }
        )

        @dataclass
        class stampedDataClass(stampDataClass, dataClass):
            f"""This class mixes {dataClass.__name__} and {stampDataClass.__name__}"""

        return stampedDataClass

    return dataClassBuilder


def BuildInteraction(actionName):
    return make_dataclass(
        actionName,
        fields=[(f"{actionName}Id", str)])


@dataclass
class HyperObject:
    groupName = "object"
    Id: str

    def __repr__(self):
        return json.dumps(asdict(self), indent=4)

    @classmethod
    def fromm(cls, m):
        kwargs = {k: v for k, v in m.items() if k in cls.__dataclass_fields__.keys()}
        return cls(**kwargs)

    def asm(self):
        return {mddb.group_key: self.groupName,
                mddb.sort_key: self.Id,
                **asdict(self)}

    def set(self):
        murd.update([self.asm()])

    class UnrecognizedObject(Exception):
        """ Exception for failing to recover a object definition """

    @classmethod
    def retrieve(cls, hoid):
        try:
            return cls.fromm(murd.read_first(group=cls.groupName, sort=hoid))
        except Exception:
            raise cls.UnrecognizedObject(f"Unable to locate HyperObject-{cls.groupName} {hoid}")

    @classmethod
    def get(cls, id=None, min_sort=None, max_sort=None, limit=200, ascending_order=False):
        return [cls.fromm(m) for m in murd.read(group=cls.groupName, sort=id, min_sort=min_sort, max_sort=max_sort, limit=limit, ascending_order=ascending_order)]


HyperBountyLegalStates = ["submitted", "verified", "confirmed", "called", "claimed", "approved", "fulfilled"]


@BuildStamp("Submitted")
@BuildStamp("Verified")
@BuildStamp("Confirmed")
@BuildStamp("Called")
@BuildStamp("Up")
@BuildStamp("Claimed")
@BuildStamp("Approved")
@BuildStamp("Fulfilled")
@dataclass
class HyperBounty(
    HyperObject,
    # *[BuildStamp(sn) for sn in hyperBountyStamps]
):
    groupName = "bounty"
    legal_states = ["submitted", "verified", "confirmed", "called", "claimed", "approved", "fulfilled"]

    State: str
    Award: str
    Name: str
    Benefactor: str
    Contact: str
    DueDate: str
    Description: str
    ReferenceMaterial: list
    ClaimedBy: str = None
    WorkCompleted: float = None
    FinalImages: list = None
    CompletionNotes: str = None
    MakerId: str = None

    @classmethod
    def fromm(cls, m):
        kwargs = {k: v for k, v in m.items() if k in cls.__dataclass_fields__.keys()}
        kwargs['Id'] = m['SORT']
        kwargs['SubmittedStamp'] = kwargs.get('SubmittedStamp', None)
        kwargs['Award'] = kwargs.get('Award', None)
        kwargs['Name'] = kwargs.get('Name', None)
        kwargs['Description'] = kwargs.get('Description', None)
        kwargs['State'] = kwargs.get('State', 'submitted')
        kwargs['DueDate'] = kwargs.get('DueDate', None)
        return cls(**kwargs)

    @classmethod
    def getByState(cls, state="confirmed"):
        assert state in cls.legal_states, f"State {state} not in legal bounty states"
        return [bounty for bounty in cls.get() if bounty.State == state]

    @property
    def sanitized_reward(self):
        sanitized_reward = self.Award
        if sanitized_reward.startswith("$"):
            sanitized_reward = sanitized_reward[1:].strip()
        try:
            return float(sanitized_reward)
        except ValueError:
            return -1.0

    @property
    def reward(self):
        if self.sanitized_reward > 0:
            return f"${self.sanitized_reward:.2f}"
        else:
            return "???"

    @property
    def MakerName(self):
        maker = HyperMaker.retrieve(self.MakerId)
        return maker.MakerName

    @property
    def sanitized_maker_email(self):
        maker = HyperMaker.retrieve(self.MakerId)
        return maker.sanitized_maker_email

    @property
    def sanitized_contact_email(self):
        return sanitize_email(self.Contact)

    @staticmethod
    def get_filetype(filename):
        return filename.split(".")[-1].lower()

    @property
    def formatted_state_str(self):
        if self.State == "confirmed":
            state = "Unmatched: 0%"
        elif self.State == "called":
            state = f"Called by: {self.MakerName}"
        else:
            state = self.State.upper()
        return state

    def get_reference_material(self, formats=None, limit=None):
        material = []
        file_list = self.ReferenceMaterial
        random.shuffle(file_list)
        for filename in file_list:
            filetype = self.get_filetype(filename)
            if filetype in formats:
                material.append(filename)
                if limit and len(material) > limit:
                    return material
        return material

    @property
    def stls(self):
        return self.get_reference_material(formats=["stl"])

    @property
    def primary_image(self):
        try:
            return self.get_reference_material(formats=["jpg", "jpeg", "png", "gif"])[0]
        except IndexError:
            return ""

    @property
    def secondary_images(self):
        formats = ["jpg", "jpeg", "png", "gif"]
        primary_image = self.primary_image
        file_list = self.FinalImages if self.FinalImages is not None else self.ReferenceMaterial
        file_list = [file
                     for file in file_list
                     if self.get_filetype(file) in formats
                     and file != primary_image]
        return file_list

    def image_path(self, image):
        return f"/bountyboard/{self.Id}/{image}"

    @property
    def ReferenceMaterialPaths(self):
        return [self.image_path(refMat) for refMat in self.ReferenceMaterial]

    @property
    def ReferenceMaterialHTML(self):
        return '<br>'.join([
            f'<img src=https://www.bountyboard.makurspace.com{self.image_path(refMatName)} alt="{self.Name}: {refMatName}" width="200" height="200">'
            for refMatName in self.ReferenceMaterial
        ])

    @property
    def FinalImagesHTML(self):
        return '<br>'.join([
            f'<img src=https://www.bountyboard.makurspace.com{self.image_path(finalImage)} alt="{self.Name}: {finalImage}" width="200" height="200">'
            for finalImage in self.FinalImages
        ])

    def set_state(self, target_state):
        assert target_state in self.legal_states
        if target_state != self.State:
            self.State = target_state
            getattr(self, f"stamp{target_state.upper()}")()
            self.set()

    def change_state(self, target_state, from_state=None):
        if from_state is not None:
            assert self.State == from_state
        assert target_state != self.State
        self.set_state(target_state)

    def approve_for_posting(self):
        assert self.State == 'verified', "Bounty not available for posting"
        self.set_state("confirmed")

    def up_bounty(self, PercentageDone, WorkCompleted, ReferenceMaterial):
        self.PercentageDone = float(PercentageDone)
        self.WorkCompleted = f"{self.WorkCompleted}\n\n{WorkCompleted}" if self.WorkCompleted is not None else WorkCompleted
        self.ReferenceMaterial = list(set(self.ReferenceMaterial + ReferenceMaterial))
        self.stampUP()
        self.set()

    def claim_bounty(self, CompletionNotes, FinalImages):
        self.FinalImages = FinalImages
        self.CompletionNotes = CompletionNotes
        self.change_state("claimed")


@dataclass
class HyperQuestion(HyperObject):  # , BuildStamp("Asked"), BuildStamp("Answered")):
    groupName = "question"
    BountyId: str
    QuestionTitle: str
    QuestionText: str
    Questioner: str
    Answer: str


@dataclass
class HyperMaker(HyperObject):
    groupName = "makers"
    MakerEmail: str
    MakerName: str
    ConfirmedContract: bool
    SapienceEvidence: str

    @classmethod
    def fromm(cls, m):
        return cls(
            MakerEmail=m['MakerEmail'],
            MakerName=m['MakerName'],
            Id=m['Id'] if 'Id' in m else m['MakerId'],
            ConfirmedContract=m['ConfirmedContract'],
            SapienceEvidence=m['SapienceEvidence'])

    @property
    def sanitized_maker_email(self):
        return sanitize_email(self.MakerEmail)

    class UnrecognizedMaker(Exception):
        """ Exception for failure to retrieve maker by email """

    @classmethod
    def retrieveByEmail(cls, email: str):
        email = sanitize_email(email)
        makers = cls.get()
        try:
            return [maker for maker in makers if maker.MakerEmail.lower() == email.lower()][0]
        except IndexError:
            raise cls.UnrecognizedMaker(f"No maker found by {email}")


@dataclass
class HyperPurchaseConfirmation:
    groupName = "purchase_confirmation"
    create_time: str
    update_time: str
    intent: str
    status: str
    payer: dict
    purchase_units: list
    links: list
