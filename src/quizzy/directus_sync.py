from typing import Dict, List

from pydantic import BaseModel
import gender_guesser.detector as gender  # type: ignore

from .icloud_contacts import read_icloud_contacts
from .vcard import VCard
from .models import (
    Adresse,
    Config,
    Contact,
    ContactsAdresse,
    Email,
    Experience,
    Organisation,
    OrganisationsAdresse,
    Telephone,
)
from .directus_backend import (
    read_contacts,
    read_adresses,
    read_contact_adresses,
    read_email,
    read_experience,
    read_organisation,
    read_organisation_adresses,
    read_telephone,
    upsert_adresse,
    upsert_contact,
    upsert_contact_adresse,
    upsert_email,
    upsert_experience,
    upsert_orga_adresse,
    upsert_organisation,
    upsert_telephone,
)


class DirectusDatabase(BaseModel):
    contacts: Dict[int, Contact] = {}
    adresses: Dict[int, Adresse] = {}
    contact_adresses: Dict[int, ContactsAdresse] = {}
    experiences: Dict[int, Experience] = {}
    organisations: Dict[int, Organisation] = {}
    organisation_adresses: Dict[int, OrganisationsAdresse] = {}
    telephones: Dict[int, Telephone] = {}
    emails: Dict[int, Email] = {}

    def list_contact_ids(self) -> List[int]:
        return list(self.contacts.keys())

    def list_adresses_ids(self) -> List[int]:
        return list(self.adresses.keys())

    def list_contact_adresses_ids(self) -> List[int]:
        return list(self.contact_adresses.keys())

    def list_experiences_ids(self) -> List[int]:
        return list(self.experiences.keys())

    def list_organisations_ids(self) -> List[int]:
        return list(self.organisations.keys())

    def list_organisation_adresses_ids(self) -> List[int]:
        return list(self.organisation_adresses.keys())

    def list_telephones_ids(self) -> List[int]:
        return list(self.telephones.keys())

    def list_emails_ids(self) -> List[int]:
        return list(self.emails.keys())

    def insert_contact(self, contact: Contact) -> int:
        scon = str(contact)
        for existing_con_id in self.contacts.keys():
            existing_con = self.contacts[existing_con_id]
            if scon == str(existing_con):
                return existing_con_id

        lids = self.list_contact_ids()
        newid = max(lids) + 1 if len(lids) > 0 else 1 if len(lids) > 0 else 1
        contact.id = newid
        self.contacts[newid] = contact
        return newid

    def insert_adresse(self, adresse: Adresse) -> int:
        sadr = str(adresse)
        for existing_adr_key in self.adresses.keys():
            existing_adr = self.adresses[existing_adr_key]
            sexisting_adr = str(existing_adr)
            if sexisting_adr == sadr:
                return existing_adr_key

        lids = self.list_adresses_ids()
        newid = max(lids) + 1 if len(lids) > 0 else 1
        adresse.id = newid
        self.adresses[newid] = adresse
        return newid

    def insert_contact_adresse(self, contact_adresses: ContactsAdresse) -> int:
        scon_adr = str(contact_adresses)
        for existing_con_ard_id in self.contact_adresses.keys():
            existing_con_adr = self.contact_adresses[existing_con_ard_id]
            if scon_adr == str(existing_con_adr):
                return existing_con_ard_id

        lids = self.list_contact_adresses_ids()
        newid = max(lids) + 1 if len(lids) > 0 else 1
        contact_adresses.id = newid
        self.contact_adresses[newid] = contact_adresses
        return newid

    def insert_experience(self, experience: Experience) -> int:
        sexp = str(experience)
        for existing_exp_id in self.experiences.keys():
            existing_exp = self.experiences[existing_exp_id]
            if sexp == str(existing_exp):
                return existing_exp_id

        lids = self.list_experiences_ids()
        newid = max(lids) + 1 if len(lids) > 0 else 1
        experience.id = newid
        self.experiences[newid] = experience
        return newid

    def insert_organisation(self, organisation: Organisation) -> int:
        sorg = str(organisation)
        for existing_org_id in self.organisations.keys():
            existing_org = self.experiences[existing_org_id]
            if sorg == str(existing_org):
                return existing_org_id

        lids = self.list_organisations_ids()
        newid = max(lids) + 1 if len(lids) > 0 else 1
        organisation.id = newid
        self.organisations[newid] = organisation
        return newid

    def insert_organisation_adresse(self, organisation_adresse: OrganisationsAdresse) -> int:
        sorg_adr = str(organisation_adresse)
        for existing_org_adr_id in self.organisation_adresses.keys():
            existing_org_adr = self.organisation_adresses[existing_org_adr_id]
            if sorg_adr == str(existing_org_adr):
                return existing_org_adr_id

        lids = self.list_organisation_adresses_ids()
        newid = max(lids) + 1 if len(lids) > 0 else 1
        organisation_adresse.id = newid
        self.organisation_adresses[newid] = organisation_adresse
        return newid

    def insert_telephone(self, telephone: Telephone) -> int:
        stel = str(telephone)
        for existing_tel_id in self.telephones.keys():
            existing_tel = self.telephones[existing_tel_id]
            if stel == str(existing_tel):
                return existing_tel_id

        lids = self.list_telephones_ids()
        newid = max(lids) + 1 if len(lids) > 0 else 1
        telephone.id = newid
        self.telephones[newid] = telephone
        return newid

    def insert_email(self, email: Email) -> int:
        smail = str(email)
        for existing_mail_id in self.emails.keys():
            existing_mail = self.emails[existing_mail_id]
            if smail == str(existing_mail):
                return existing_mail_id

        lids = self.list_emails_ids()
        newid = max(lids) + 1 if len(lids) > 0 else 1
        email.id = newid
        self.emails[newid] = email
        return newid

    def load_from_icloud(self, config: Config):
        d = gender.Detector()
        for icontact in read_icloud_contacts(config):
            filtered_url: List[str]
            if icontact.urls is None:
                filtered_url = []
            else:
                filtered_url = [
                    iurl.field for iurl in icontact.urls if not iurl.field.startswith("uphabit://")
                ]

            Civilite, Prenom, Particule, Nom = icontact.analyse_name(d)

            contact = Contact(
                Nom=Nom,
                Prenom=Prenom,
                Particule=Particule.value,
                Civilite=Civilite,
                Nom_de_naissance="",
                Date_de_naissance=icontact.birthday,
                Site_web=filtered_url[0] if len(filtered_url) > 0 else "",
                Notes=icontact.notes,
                Photo=icontact.photo.url if icontact.photo is not None else None,
                # TODO Download photo raw bytes
                # TODO Fill other directus tables
            )

            cid = self.insert_contact(contact)

            # Storing addresses
            for iadr in icontact.streetAddresses:
                if iadr.label == "WORK":
                    continue

                adr = Adresse(
                    Adresse=iadr.field.street,
                    Code_postal=iadr.field.postalCode,
                    Ville=iadr.field.city,
                    Pays=iadr.field.country,
                )
                aid = self.insert_adresse(adr)
                con_adr = ContactsAdresse(Contacts_id=cid, Adresse_id=aid, Type=iadr.label)
                caid = self.insert_contact_adresse(con_adr)
                contact.Adresses.append(caid)

            # Storing last experience
            if icontact.companyName is not None and icontact.companyName != "":
                orgid = None
                orga = Organisation(
                    Nom=icontact.companyName,
                    Type="Entreprise",
                )

                for eorgid in self.organisations.keys():
                    if icontact.companyName == self.organisations[eorgid]:
                        orgid = eorgid

                if orgid is None:
                    orgid = self.insert_organisation(orga)

                orga.id = orgid
                for iadr in icontact.streetAddresses:
                    if iadr.label != "WORK":
                        continue

                    adr = Adresse(
                        Adresse=iadr.field.street,
                        Code_postal=iadr.field.postalCode,
                        Ville=iadr.field.city,
                        Pays=iadr.field.country,
                    )
                    aid = self.insert_adresse(adr)
                    org_adr = OrganisationsAdresse(Organisation_id=orgid, Adresse_id=aid)
                    self.insert_organisation_adresse(org_adr)
                    orga.Adresse.append(aid)

                expe = Experience(
                    Contact=cid,
                    Type="Professionnel",
                    Organisation=orgid,
                    Intitule=icontact.jobTitle,
                )
                self.insert_experience(expe)

            # Storing telephones
            if icontact.phones is not None:
                for itel in icontact.phones:
                    tel = Telephone(
                        Telephone=itel.field, Contact=cid, Prefere=False, Type=itel.label
                    )
                    self.insert_telephone(tel)

            # Storing emails
            if icontact.emailAddresses is not None:
                for imail in icontact.emailAddresses:
                    mail = Email(Email=imail.field, Contact=cid, Prefere=False, Type=imail.label)
                    self.insert_email(mail)

    def upsert_directus(self, config: Config):
        upsert_contact(config, self.contacts.values())
        upsert_adresse(config, self.adresses.values())
        upsert_email(config, self.emails.values())
        upsert_organisation(config, self.organisations.values())
        upsert_telephone(config, self.telephones.values())
        upsert_experience(config, self.experiences.values())
        upsert_contact_adresse(config, self.contact_adresses.values())
        upsert_orga_adresse(config, self.organisation_adresses.values())

    def load_from_directus(self, config: Config):
        for contact in read_contacts(config):
            self.contacts[contact.id] = contact

        for adresse in read_adresses(config):
            self.adresses[adresse.id] = adresse

        for con_adr in read_contact_adresses(config):
            self.contact_adresses[con_adr.id] = con_adr

        for expe in read_experience(config):
            self.experiences[expe.id] = expe

        for orga in read_organisation(config):
            self.organisations[orga.id] = orga

        for orga_adr in read_organisation_adresses(config):
            self.organisation_adresses[orga_adr.id] = orga_adr

        for tel in read_telephone(config):
            self.telephones[tel.id] = tel

        for mail in read_email(config):
            self.emails[mail.id] = mail

    def convert_contacts(self) -> List[VCard]:
        list_vcard: List[VCard] = []
        for contact in self.contacts.values():
            vcard = contact.to_vcard(
                self.adresses,
                self.contact_adresses,
                self.experiences,
                self.organisations,
                self.organisation_adresses,
                self.telephones,
                self.emails,
            )
            list_vcard.append(vcard)

        return list_vcard
