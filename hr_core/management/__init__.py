from decimal import Decimal
import datetime

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model

from hr_about.models import CarouselSlide, PullQuote
from hr_live.models import (
    Day,
    Venue,
    Booker,
    Musician,
    Act,
    Show,
)
from hr_common.models import Address
from hr_shop.models import (
    Product,
    ProductVariant,
    ProductOptionType,
    ProductOptionValue,
    OptionTypeTemplate,
    OptionValueTemplate,
    ProductVariantOption,
    InventoryItem,
)


User = get_user_model()


class Command(BaseCommand):
    help = "Seed demo/dev data for hr_about, hr_live, and hr_shop."

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("Seeding demo data…"))

        self._seed_hr_about()
        self._seed_hr_live()
        self._seed_hr_shop()

        self.stdout.write(self.style.SUCCESS("Demo data seeding complete."))


# -------------------------------------------------------------------------
    # hr_live
    # -------------------------------------------------------------------------
    def _seed_hr_live(self):
        self.stdout.write("  → hr_live…")

        # Days of week (if not already present)
        day_map = {code: label for code, label in Day.DAY_CHOICES}
        existing_days = set(Day.objects.values_list("name", flat=True))
        for code, label in day_map.items():
            if code not in existing_days:
                Day.objects.create(name=code)
        self.stdout.write("    • Ensured Day records exist.")

        # One booker
        booker, created = Booker.objects.get_or_create(
            first_name="Casey",
            last_name="Signals",
            defaults={
                "phone_number": "+16125550101",
                "email": "casey.bookings@example.com",
                "note": "Primary booking contact for Hella Reptilian.",
            },
        )
        if created:
            self.stdout.write(f"    • Created Booker: {booker.full_name}")
        else:
            self.stdout.write("    • Booker already exists; using existing.")

        # Addresses & Venues
        venues_to_create = [
            {
                "venue_name": "The Drift Bar",
                "addr": dict(
                    street_address="100 River Drift Ln",
                    city="Minneapolis",
                    subdivision="MN",
                    postal_code="55401",
                    country="USA",
                ),
                "venue": dict(
                    website="https://drift-bar.example.com",
                    phone_number="+16125550111",
                    email="info@drift-bar.example.com",
                    note="Small room, loud P.A., cheap beer.",
                ),
            },
            {
                "venue_name": "Satellite Lounge",
                "addr": dict(
                    street_address="42 Orbit Ave",
                    city="St. Paul",
                    subdivision="MN",
                    postal_code="55101",
                    country="USA",
                ),
                "venue": dict(
                    website="https://satellite-lounge.example.com",
                    phone_number="+16515550122",
                    email="booking@satellite-lounge.example.com",
                    note="Good stage lighting, sketchy backstage.",
                ),
            },
        ]

        venues = []
        for spec in venues_to_create:
            addr_data = spec["addr"]
            addr, _ = Address.objects.get_or_create(**addr_data)

            venue, created_v = Venue.objects.get_or_create(
                name=spec["venue_name"],
                defaults={
                    "address": addr,
                    **spec["venue"],
                },
            )

            # Make sure address/note stay in sync on repeated runs
            if not created_v:
                venue.address = addr
                for k, v in spec["venue"].items():
                    setattr(venue, k, v)
                venue.save()

            # attach booker
            venue.add_booker(booker)

            venues.append(venue)

        self.stdout.write(f"    • Ensured {len(venues)} Venue records exist and linked to booker.")

        # Musicians
        musician_specs = [
            ("Jake", "Boline", "+16125550201", "jake@example.com"),
            ("Rae", "Voltage", "+16125550202", "rae@example.com"),
            ("Mira", "Drift", "+16125550203", "mira@example.com"),
            ("Owen", "Collapse", "+16125550204", "owen@example.com"),
            ("Tess", "Static", "+16125550205", "tess@example.com"),
            ("Nico", "Phase", "+16125550206", "nico@example.com"),
        ]
        musicians = []
        for first, last, phone, email in musician_specs:
            m, _ = Musician.objects.get_or_create(
                first_name=first,
                last_name=last,
                defaults={
                    "phone_number": phone,
                    "email": email,
                    "note": "Demo seed musician.",
                },
            )
            musicians.append(m)
        self.stdout.write(f"    • Ensured {len(musicians)} Musician records exist.")

        # Acts (3–4 acts, shared members)
        acts_def = [
            {
                "name": "Hella Reptilian",
                "website": "https://hella-reptilian.example.com",
                "members": ["Jake Boline", "Rae Voltage", "Mira Drift"],
                "contacts": ["Jake Boline"],
                "note": "Main band.",
            },
            {
                "name": "Phase Collapse",
                "website": "https://phase-collapse.example.com",
                "members": ["Owen Collapse", "Tess Static"],
                "contacts": ["Owen Collapse", "Tess Static"],
                "note": "Side project, heavier and noisier.",
            },
            {
                "name": "Drift Signal",
                "website": "https://drift-signal.example.com",
                "members": ["Mira Drift", "Nico Phase"],
                "contacts": ["Mira Drift"],
                "note": "Ambient/drone duo.",
            },
            {
                "name": "Static Transit",
                "website": "https://static-transit.example.com",
                "members": ["Rae Voltage", "Tess Static", "Nico Phase"],
                "contacts": ["Tess Static"],
                "note": "Weird synth rock.",
            },
        ]

        def _find_musician(full_name: str):
            first, *rest = full_name.split(" ")
            last = " ".join(rest) if rest else ""
            return Musician.objects.get(first_name=first, last_name=last)

        acts = []
        for spec in acts_def:
            act, created_a = Act.objects.get_or_create(
                name=spec["name"],
                defaults={
                    "website": spec["website"],
                    "note": spec["note"],
                },
            )
            if not created_a:
                act.website = spec["website"]
                act.note = spec["note"]
                act.save()

            # members
            member_objs = [_find_musician(n) for n in spec["members"]]
            contact_objs = [_find_musician(n) for n in spec["contacts"]]
            act.members.set(member_objs)
            act.contacts.set(contact_objs)
            acts.append(act)

        self.stdout.write(f"    • Ensured {len(acts)} Act records exist with members/contacts.")

        # Shows: 4 dates in the future
        if not Show.objects.exists():
            today = timezone.now().date()
            base_time = datetime.time(hour=20, minute=0)

            show_specs = [
                {
                    "delta_days": 7,
                    "venue": venues[0],
                    "lineup": [acts[0], acts[1]],
                    "status": "published",
                },
                {
                    "delta_days": 21,
                    "venue": venues[1],
                    "lineup": [acts[0], acts[2]],
                    "status": "published",
                },
                {
                    "delta_days": 35,
                    "venue": venues[0],
                    "lineup": [acts[1], acts[3]],
                    "status": "draft",
                },
                {
                    "delta_days": 60,
                    "venue": venues[1],
                    "lineup": [acts[0], acts[1], acts[2], acts[3]],
                    "status": "draft",
                },
            ]

            for spec in show_specs:
                date = today + datetime.timedelta(days=spec["delta_days"])
                show = Show.objects.create(
                    date=date,
                    time=base_time,
                    timezone="America/Chicago",
                    venue=spec["venue"],
                    booker=booker,
                    status=spec["status"],
                    created_by=None,
                    modified_by=None,
                )
                show.lineup.set(spec["lineup"])

            self.stdout.write("    • Created 4 Show records.")
        else:
            self.stdout.write("    • Show records already exist; skipping.")