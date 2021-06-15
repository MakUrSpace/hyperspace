from typing import ClassVar
from datetime import datetime
from dataclasses import dataclass, asdict

from hyperspace.utilities import sanitize_email
from hyperspace.murd import mddb, murd, purchase_murd


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

    @classmethod
    def fromm(cls, m):
        kwargs = {k: v for k, v in m.items() if k not in [mddb.group_key, mddb.sort_key, "CREATE_TIME"]}
        kwargs['BountyId'] = kwargs['BountyName'] if 'BountyId' not in m else kwargs['BountyId']
        bounty = cls(**kwargs)
        return bounty

    def asm(self):
        return {**{mddb.group_key: self.State,
                   mddb.sort_key: self.BountyId,
                   "CREATE_TIME": datetime.utcnow().isoformat()},
                **self.asdict()}

    def asdict(self):
        return asdict(self)

    def store(self):
        murd.update([self.asm()])

    def change_state(self, target_state):
        assert target_state in Bounty.states
        orig = self.asm()
        self.State = target_state
        self.store()
        murd.delete([orig])

    @property
    def primary_image(self):
        formats = ["jpg", "jpeg", "png"]
        for refmat in self.ReferenceMaterial:
            filetype = refmat.split(".")[-1]
            if filetype in formats:
                return refmat
        return None

    def image_path(self, image):
        return f"/bountyboard/{self.BountyId}/{image}"

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
        raise Exception(f"{bounty_id} not found")

    @classmethod
    def get_bounties(cls, group="confirmed", limit=200):
        return [cls.fromm(b) for b in murd.read(group=group, limit=limit)]


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

    @classmethod
    def retrieve(cls, maker_email):
        return cls.fromm(murd.read_first(group="makers", sort=sanitize_email(maker_email)))
