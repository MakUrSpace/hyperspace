import json
from typing import ClassVar
from datetime import datetime
from dataclasses import dataclass, asdict, make_dataclass
import random

from hyperspace.utilities import sanitize_email, timestamp
from hyperspace.murd import mddb, murd, purchase_murd


def BuildStamp(stampName):
    return make_dataclass(
        stampName,
        fields=[(f"{stampName.capitalize()}Stamp", str)],
        namespace={
            f"stamp{stampName.upper()}": lambda self: setattr(self, f"{stampName}Stamp", timestamp()),
            f"timeSince{stampName.upper()}":
                lambda self:
                    None
                    if not (stamp := getattr(self, f"{stampName}Stamp")) else
                    (datetime.utcnow() - datetime.fromisoformat(stamp).total_seconds())
        }
    )


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
    def mkeys(cls, m):
        return {
            "Id": m["Id"]
        }

    @classmethod
    def fromm(cls, m):
        return cls(**cls.mkeys(m))

    def asm(self):
        return {mddb.group_key: self.groupName,
                mddb.sort_key: self.Id,
                **asdict(self)}

    def store(self):
        murd.update([self.asm()])

    class UnrecognizedObject(Exception):
        """ Exception for failing to recover a object definition """

    @classmethod
    def retrieve(cls, hid):
        try:
            return cls.fromm(murd.read_first(group=cls.groupName, sort=hid))
        except Exception:
            raise cls.UnrecognizedObject(f"Unable to locate HyperObject-{cls.groupName} {hid}")

    @classmethod
    def get(cls, limit=200):
        return [cls.fromm(m) for m in murd.read(group=cls.groupName, limit=limit)]



hyperBountyStamps = ["Submission", "Confirmed", "Called", "Claimed", "Up", "submitted", "confirmed", "called", "claimed"]


@dataclass
class HyperBounty(
    HyperObject,
    *[BuildStamp(sn) for sn in hyperBountyStamps]
):
    groupName = "bounty"
    State: str
    legal_states = ["submitted", "confirmed", "called", "claimed"]
    Award: str
    Name: str
    Benefactor: str
    Contact: str
    Description: str
    ReferenceMaterial: list
    ClaimedBy: str
    WorkCompleted: float
    FinalImages: list
    CompletionNotes: str

    @classmethod
    def mkeys(cls, m):
        return {**super().mkeys(m),
                "State": m["State"],
                "Award": m["Award"],
                "Name": m["Name"],
                "Benefactor": m["Benefactor"],
                "Contact": m["Contact"],
                "ReferenceMaterial": m["ReferenceMaterial"],
                "Description": m["Description"],
                "ClaimedBy": m.get("ClaimedBy", None),
                "WorkCompleted": m.get("WorkCompleted", 0),
                "FinalImages": m.get("FinalImages", []),
                "CompletionNotes": m.get("CompletionNotes", ""),
                **{(stampName := f"{stamp.capitalize()}Stamp"): m.get(stampName, None)
                   for stamp in hyperBountyStamps}}
    
    @property
    def sanitized_reward(self):
        sanitized_reward = self.Award
        if sanitized_reward.startswith("$"):
            sanitized_reward = sanitized_reward[1:].strip()
        try:
            return float(sanitized_reward)
        except ValueError:
            return 9999.99

    @property
    def reward(self):
        return f"${self.sanitized_reward:.2f}"

    @property
    def sanitized_contact(self):
        return sanitize_email(self.Contact)

    @property
    def sanitized_maker_email(self):
        return sanitize_email(self.MakerEmail)

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

    @property
    def primary_image(self):
        if self.lazy_primary_image is not None:
            return self.lazy_primary_image
        else:
            formats = ["jpg", "jpeg", "png"]
            file_list = self.FinalImages if self.FinalImages is not None else self.ReferenceMaterial
            random.shuffle(file_list)
            for filename in file_list:
                filetype = self.get_filetype(filename)
                if filetype in formats:
                    self.lazy_primary_image = filename
                    return self.lazy_primary_image
            return None

    @property
    def secondary_images(self):
        formats = ["jpg", "jpeg", "png"]
        file_list = self.FinalImages if self.FinalImages is not None else self.ReferenceMaterial
        file_list = [file
                     for file in file_list
                     if self.get_filetype(file) in formats and file != self.primary_image]
        return file_list

    def image_path(self, image):
        return f"/bountyboard/{self.Id}/{image}"

    @property
    def ReferenceMaterialPaths(self):
        return [self.image_path(refMat) for refMat in self.ReferenceMaterial]

    @property
    def ReferenceMaterialHTML(self):
        return '<br>'.join([
            f'<img src=https://www.makurspace.com{self.image_path(refMatName)} alt="{self.BountyName}: {refMatName}" width="200" height="200">'
            for refMatName in self.ReferenceMaterial
        ])

    def set_state(self, target_state):
        assert target_state in self.legal_states
        if target_state != self.State:
            self.State = target_state
            getattr(self, f"stamp{target_state.upper()}")()
            self.store()

    def change_state(self, target_state, from_state=None):
        if from_state is not None:
            assert self.State == from_state
        assert target_state != self.State
        self.set_state(target_state)

    def up_bounty(self, PercentageDone, WorkCompleted, ReferenceMaterial):
        self.PercentageDone = float(PercentageDone)
        self.WorkCompleted = f"{self.WorkCompleted}\n\n{WorkCompleted}" if self.WorkCompleted is not None else WorkCompleted
        self.ReferenceMaterial = list(set(self.ReferenceMaterial + ReferenceMaterial))
        self.stampUP()
        self.store()

    def claim_bounty(self, CompletionNotes, FinalImages):
        self.FinalImages = FinalImages
        self.CompletionNotes = CompletionNotes
        self.change_state("claimed")


def oldBtoNew(o):
    changed_keys = {
        "Id": "BountyId",
        "Name": "BountyName",
        "Award": "Bounty",
        "Description": "BountyDescription"
    }
    return {
        **{k: o[v] for k, v in changed_keys.items()},
        **{k: v for k, v in o.items() if k not in changed_keys.values()}
    }


@dataclass
class HyperQuestion(BuildStamp("Asked"), BuildStamp("Answered")):
    groupName = "question"
    QuestionId: str
    BountyId: str
    QuestionTitle: str
    QuestionText: str
    Questioner: bool
    Answer: str


@dataclass
class HyperMaker(HyperObject):
    groupName = "maker"
    MakerEmail: str
    MakerName: str
    ConfirmedContract: bool

    @classmethod
    def fromm(cls, m):
        return cls(MakerEmail=m['MakerEmail'], MakerName=m['MakerName'], Id=m['Id'], ConfirmedContract=m['ConfirmedContract'])

    @property
    def sanitized_maker_email(self):
        return sanitize_email(self.MakerEmail)


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


@dataclass
class Bounty:
    BountyId: str
    Bounty: str
    BountyName: str
    Benefactor: str
    Contact: str
    BountyDescription: str
    ReferenceMaterial: list
    ConfirmationId: str = ""
    MakerName: str = ""
    MakerEmail: str = ""
    State: str = "submitted"
    states: ClassVar = ["submitted", "confirmed", "called", "claimed"]
    SubmissionStamp: str = None
    ConfirmedStamp: str = None
    CalledStamp: str = None
    UpStamp: str = None
    WipStamp: str = None
    ClaimedStamp: str = None
    PercentageDone: float = 0
    WorkCompleted: str = ""
    FinalImages: list = None

    lazy_primary_image = None

    def __post_init__(self):
        if self.WipStamp is not None:
            self.UpStamp = self.WipStamp
            self.WipStamp = None

        if self.SubmissionStamp is None:
            self.SubmissionStamp = timestamp()

    @property
    def sanitized_reward(self):
        sanitized_reward = self.Bounty
        if sanitized_reward.startswith("$"):
            sanitized_reward = sanitized_reward[1:].strip()
        try:
            return float(sanitized_reward)
        except ValueError:
            return 9999.99

    @property
    def reward(self):
        return f"${self.sanitized_reward:.2f}"

    @property
    def sanitized_contact(self):
        return sanitize_email(self.Contact)

    @property
    def sanitized_maker_email(self):
        return sanitize_email(self.MakerEmail)

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

    @property
    def primary_image(self):
        if self.lazy_primary_image is not None:
            return self.lazy_primary_image
        else:
            formats = ["jpg", "jpeg", "png"]
            file_list = self.FinalImages if self.FinalImages is not None else self.ReferenceMaterial
            random.shuffle(file_list)
            for filename in file_list:
                filetype = self.get_filetype(filename)
                if filetype in formats:
                    self.lazy_primary_image = filename
                    return self.lazy_primary_image
            return None

    @property
    def secondary_images(self):
        formats = ["jpg", "jpeg", "png"]
        file_list = self.FinalImages if self.FinalImages is not None else self.ReferenceMaterial
        file_list = [file
                     for file in file_list
                     if self.get_filetype(file) in formats and file != self.primary_image]
        return file_list

    def image_path(self, image):
        return f"/bountyboard/{self.BountyId}/{image}"

    @property
    def ReferenceMaterialPaths(self):
        return [self.image_path(refMat) for refMat in self.ReferenceMaterial]

    @property
    def ReferenceMaterialHTML(self):
        return '<br>'.join([
            f'<img src=https://www.makurspace.com{self.image_path(refMatName)} alt="{self.BountyName}: {refMatName}" width="200" height="200">'
            for refMatName in self.ReferenceMaterial
        ])

    @staticmethod
    def bounty_exists(bounty, all_states=False):
        check_states = [bounty.State] if not all_states else Bounty.states[::-1]
        for state in check_states:
            if murd.read(group=state, sort=bounty.BountyName):
                return state

    @classmethod
    def get_bounty(cls, bounty_id):
        for state in cls.states[::-1]:
            try:
                return cls.fromm(murd.read(group=state, sort=bounty_id)[0])
            except Exception:
                pass
        print("AWASDFASDF")
        print(bounty_id)
        raise Exception(f'{bounty_id} not found')

    @classmethod
    def get_bounties(cls, group="confirmed", limit=200):
        return [cls.fromm(b) for b in murd.read(group=group, limit=limit)]

    @classmethod
    def fromm(cls, m):
        kwargs = {k: v for k, v in m.items() if k not in [mddb.group_key, mddb.sort_key, "CREATE_TIME"]}
        kwargs['BountyId'] = kwargs['BountyName'] if 'BountyId' not in m else kwargs['BountyId']
        if 'PercentageDone' in kwargs:
            kwargs['PercentageDone'] = float(kwargs['PercentageDone'])
        else:
            kwargs['PercentageDone'] = 0
        bounty = cls(**kwargs)
        return bounty

    def __repr__(self):
        return json.dumps(asdict(self), indent=4)

    def asdict(self):
        return asdict(self)

    def asm(self):
        return {**{mddb.group_key: self.State,
                   mddb.sort_key: self.BountyId,
                   "CREATE_TIME": datetime.utcnow().isoformat()},
                **self.asdict(),
                "PercentageDone": json.dumps(self.PercentageDone)}

    def set_state(self, target_state):
        assert target_state in Bounty.states
        if target_state != self.State:
            orig = self.asm()
            self.State = target_state
            setattr(self, f"{target_state.capitalize()}Stamp", timestamp())
            self.store()
            murd.delete([orig])

    def change_state(self, target_state, from_state=None):
        if from_state is not None:
            assert self.State == from_state
        assert target_state != self.State
        self.set_state(target_state)

    def store(self):
        murd.update([self.asm()])

    def get_stamp(self, state=None):
        assert state in self.states + ["up"]
        return getattr(self, f"{state.capitalize()}Stamp")

    def time_since(self, state=None):
        """Return the time since a state's stamp in seconds"""
        if state is None:
            for state in self.states:
                if self.get_stamp(state) is not None:
                    break
        stamp_string = self.get_stamp(state)
        if stamp_string is None:
            return None
        return (datetime.utcnow() - datetime.fromisoformat(stamp_string)).total_seconds()

    def up_bounty(self, PercentageDone, WorkCompleted, ReferenceMaterial):
        self.PercentageDone = float(PercentageDone)
        self.WorkCompleted = f"{self.WorkCompleted}\n\n{WorkCompleted}" if self.WorkCompleted is not None else WorkCompleted
        self.ReferenceMaterial = list(set(self.ReferenceMaterial + ReferenceMaterial))
        setattr(self, f"UpStamp", timestamp())
        self.store()

    def claim_bounty(self, CompletionNotes, FinalImages):
        self.FinalImages = FinalImages
        self.CompletionNotes = CompletionNotes
        self.change_state("claimed")


@dataclass
class PurchaseConfirmation:
    create_time: str
    update_time: str
    id: str
    intent: str
    status: str
    payer: dict
    purchase_units: list
    links: list

    def asm(self):
        return {**{mddb.group_key: "purchase_confirmation",
                   mddb.sort_key: self.id},
                **self.asdict()}

    @classmethod
    def fromm(cls, m):
        bounty = cls(**{k: v for k, v in m.items() if k not in [mddb.group_key, mddb.sort_key]})
        return bounty

    def asdict(self):
        return asdict(self)

    def store(self):
        purchase_murd.update([self.asm()])


@dataclass
class Maker:
    MakerEmail: str
    MakerName: str
    MakerId: str
    ConfirmedContract: bool

    @classmethod
    def fromm(cls, m):
        return cls(MakerEmail=m['MakerEmail'], MakerName=m['MakerName'], MakerId=m['MakerId'], ConfirmedContract=m['ConfirmedContract'])

    @property
    def sanitized_maker_email(self):
        return sanitize_email(self.MakerEmail)

    def asm(self):
        return {mddb.group_key: "makers", mddb.sort_key: self.MakerEmail, **asdict(self)}

    def store(self):
        murd.update([self.asm()])

    class UnrecognizedMaker(Exception):
        """ Exception for failing to recover a Maker definition """

    @classmethod
    def retrieve(cls, maker_email):
        maker_email = sanitize_email(maker_email)
        try:
            return cls.fromm(murd.read_first(group="makers", sort=maker_email))
        except Exception:
            raise cls.UnrecognizedMaker(f"Unable to locate Maker {maker_email}")

    @classmethod
    def get_makers(cls, limit=200):
        return [cls.fromm(b) for b in murd.read(group="makers", limit=limit)]


@dataclass
class Question(BuildStamp("Asked"), BuildStamp("Answered")):
    QuestionId: str
    BountyId: str
    QuestionTitle: str
    QuestionText: str
    Questioner: bool
    Answer: str

    groupName = "question"

    @classmethod
    def fromm(cls, m):
        return cls(QuestionId=m['QuestionId'], BountyId=m['BountyId'], QuestionTitle=m['QuestionTitle'],
                   QuestionText=m['QuestionText'], Questioner=m['Questioner'], Answer=m['Answer'],
                   **{(stampName := f"{stamp}Stamp"): m[stampName] if stampName in m else None
                      for stamp in ["Asked", "Answered"]})

    @property
    def sanitized_questioner(self):
        return sanitize_email(self.MakerEmail)

    def asm(self):
        return {mddb.group_key: self.groupName, mddb.sort_key: self.QuestionId, **asdict(self)}

    def store(self):
        murd.update([self.asm()])


    @classmethod
    def get(cls, limit=200):
        return [cls.fromm(b) for b in murd.read(group=cls.groupName, limit=limit)]
