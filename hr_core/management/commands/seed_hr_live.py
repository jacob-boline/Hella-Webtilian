# hr_core/management/commands/seed_hr_live.py

from pathlib import Path
from datetime import date as Date, time as Time

import yaml
from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand

from hr_common.models import Address
from hr_live.models import Day, Venue, Booker, Musician, Act, Show


class Command(BaseCommand):
    help = "Seed hr_live data (bookers, venues, musicians, acts, shows) from seed_data/hr_live/live.yml."

    def handle(self, *args, **options):
        self._seed_hr_live()

    # ==============================
    # hr_live seeding
    # ==============================
    def _seed_hr_live(self):
        base = Path(settings.BASE_DIR) / "_seed_data" / "hr_live"
        if not base.exists():
            self.stdout.write(
                self.style.WARNING(f"  → No seed_data/hr_live directory found at {base}")
            )
            return

        live_yml = base / "live.yml"
        if not live_yml.exists():
            self.stdout.write(
                self.style.WARNING(f"  → No live.yml found in {base}; nothing to seed.")
            )
            return

        cfg = yaml.safe_load(live_yml.read_text()) or {}

        self.stdout.write("  → hr_live…")

        self._ensure_days()

        # Maps for cross-references
        booker_map = self._seed_bookers(cfg.get("bookers") or [])
        venue_map = self._seed_venues(cfg.get("venues") or [], booker_map)
        musician_map = self._seed_musicians(cfg.get("musicians") or [])
        act_map = self._seed_acts(cfg.get("acts") or [], musician_map)
        self._seed_shows(cfg.get("shows") or [], base, venue_map, booker_map, act_map)

        self.stdout.write("    • hr_live seed data applied.")

    # ------------------------------------------------------
    # Days of week
    # ------------------------------------------------------
    def _ensure_days(self):
        """
        Ensure MON–SUN Day rows exist.
        """
        codes = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
        existing = set(Day.objects.values_list("name", flat=True))

        created_any = False
        for code in codes:
            if code not in existing:
                Day.objects.create(name=code)
                created_any = True

        if created_any:
            self.stdout.write("    • Ensured Day entries (MON–SUN).")

    # ------------------------------------------------------
    # Bookers
    # ------------------------------------------------------
    def _seed_bookers(self, bookers_cfg):
        """
        bookers:
          - key: "main_booker"
            first_name: "Jamie"
            last_name: "Signals"
            phone_number: "+1612..."
            email: "booking@..."
            note: "..."
        """
        self.stdout.write("    • Seeding Bookers…")
        key_map = {}

        for idx, b in enumerate(bookers_cfg, start=1):
            key = b.get("key") or f"booker_{idx}"
            first = b.get("first_name") or "Booker"
            last = b.get("last_name") or ""
            phone = b.get("phone_number") or None
            email = b.get("email") or None
            note = b.get("note") or ""

            # Use (email) if present, otherwise (first,last,phone) as identifier
            if email:
                lookup = {"email": email}
            else:
                lookup = {"first_name": first, "last_name": last, "phone_number": phone}

            booker, created = Booker.objects.get_or_create(
                **lookup,
                defaults={
                    "first_name": first,
                    "last_name": last,
                    "phone_number": phone,
                    "email": email,
                    "note": note,
                },
            )
            if not created:
                booker.first_name = first
                booker.last_name = last
                booker.phone_number = phone
                booker.email = email
                booker.note = note
                booker.save(update_fields=["first_name", "last_name", "phone_number", "email", "note"])

            key_map[key] = booker

        return key_map

    # ------------------------------------------------------
    # Venues + Addresses
    # ------------------------------------------------------
    def _seed_venues(self, venues_cfg, booker_map):
        """
        venues:
          - name: "The Dive Rift"
            website: "https://..."
            phone_number: "+1..."
            email: "info@..."
            note: "..."
            bookers: ["main_booker"]
            address:
              street_address: "123 Main"
              city: "Minneapolis"
              subdivision: "MN"
              postal_code: "55401"
              country: "USA"
        """
        self.stdout.write("    • Seeding Venues…")
        venue_map = {}

        for v in venues_cfg:
            name = v.get("name")
            if not name:
                self.stdout.write(
                    self.style.WARNING("      (Skipping venue with no name.)")
                )
                continue

            website = v.get("website") or ""
            phone = v.get("phone_number") or None
            email = v.get("email") or None
            note = v.get("note") or ""

            addr_cfg = v.get("address") or {}
            street = addr_cfg.get("street_address") or ""
            city = addr_cfg.get("city") or ""
            subdivision = addr_cfg.get("subdivision") or ""
            postal_code = addr_cfg.get("postal_code") or ""
            country = addr_cfg.get("country") or "USA"

            address = None
            if street and city and subdivision:
                address, _ = Address.objects.get_or_create(
                    street_address=street,
                    city=city,
                    subdivision=subdivision,
                    defaults={
                        "postal_code": postal_code,
                        "country": country,
                    },
                )
                # update zip/country if changed
                changed = False
                if postal_code and address.postal_code != postal_code:
                    address.postal_code = postal_code
                    changed = True
                if country and address.country != country:
                    address.country = country
                    changed = True
                if changed:
                    address.save(update_fields=["postal_code", "country"])

            venue, created = Venue.objects.get_or_create(
                name=name,
                defaults={
                    "website": website,
                    "phone_number": phone,
                    "email": email,
                    "note": note,
                    "address": address,
                },
            )
            if not created:
                venue.website = website
                venue.phone_number = phone
                venue.email = email
                venue.note = note
                venue.address = address
                venue.save(update_fields=["website", "phone_number", "email", "note", "address"])

            # Attach bookers (M2M)
            booker_keys = v.get("bookers") or []
            if booker_keys:
                venue.bookers.clear()
                for bk in booker_keys:
                    bobj = booker_map.get(bk)
                    if not bobj:
                        self.stdout.write(
                            self.style.WARNING(
                                f"      (Venue '{name}' references unknown booker key '{bk}'.)"
                            )
                        )
                        continue
                    venue.bookers.add(bobj)

            venue_map[name] = venue

        return venue_map

    # ------------------------------------------------------
    # Musicians
    # ------------------------------------------------------
    def _seed_musicians(self, musicians_cfg):
        """
        musicians:
          - key: "jacob"
            first_name: "Jacob"
            last_name: "Boline"
            phone_number: "+1..."
            email: "..."
            note: "Guitar / vox"
        """
        self.stdout.write("    • Seeding Musicians…")
        key_map = {}

        for idx, m in enumerate(musicians_cfg, start=1):
            key = m.get("key") or f"musician_{idx}"
            first = m.get("first_name") or "Musician"
            last = m.get("last_name") or ""
            phone = m.get("phone_number") or None
            email = m.get("email") or None
            note = m.get("note") or ""

            if email:
                lookup = {"email": email}
            else:
                lookup = {"first_name": first, "last_name": last, "phone_number": phone}

            musician, created = Musician.objects.get_or_create(
                **lookup,
                defaults={
                    "first_name": first,
                    "last_name": last,
                    "phone_number": phone,
                    "email": email,
                    "note": note,
                },
            )
            if not created:
                musician.first_name = first
                musician.last_name = last
                musician.phone_number = phone
                musician.email = email
                musician.note = note
                musician.save(update_fields=["first_name", "last_name", "phone_number", "email", "note"])

            key_map[key] = musician

        return key_map

    # ------------------------------------------------------
    # Acts
    # ------------------------------------------------------
    def _seed_acts(self, acts_cfg, musician_map):
        """
        acts:
          - name: "Hella Reptilian!"
            website: "https://..."
            note: "Main project."
            members: ["jacob", "drummer"]
            contacts: ["jacob"]
        """
        self.stdout.write("    • Seeding Acts…")
        act_map = {}

        for a in acts_cfg:
            name = a.get("name")
            if not name:
                self.stdout.write(
                    self.style.WARNING("      (Skipping act with no name.)")
                )
                continue

            website = a.get("website") or f"band{acts_cfg.index(a)}.com"
            note = a.get("note") or ""

            act, created = Act.objects.get_or_create(
                name=name,
                defaults={
                    "website": website,
                    "note": note,
                },
            )
            if not created:
                act.website = website
                act.note = note
                act.save(update_fields=["website", "note"])

            # M2M members
            member_keys = a.get("members") or []
            if member_keys:
                act.members.clear()
                for mk in member_keys:
                    mobj = musician_map.get(mk)
                    if not mobj:
                        self.stdout.write(
                            self.style.WARNING(
                                f"      (Act '{name}' references unknown musician key '{mk}' in members.)"
                            )
                        )
                        continue
                    act.members.add(mobj)

            # M2M contacts
            contact_keys = a.get("contacts") or []
            if contact_keys:
                act.contacts.clear()
                for ck in contact_keys:
                    cobj = musician_map.get(ck)
                    if not cobj:
                        self.stdout.write(
                            self.style.WARNING(
                                f"      (Act '{name}' references unknown musician key '{ck}' in contacts.)"
                            )
                        )
                        continue
                    act.contacts.add(cobj)

            act_map[name] = act

        return act_map

    # ------------------------------------------------------
    # Shows
    # ------------------------------------------------------
    def _seed_shows(self, shows_cfg, base: Path, venue_map, booker_map, act_map):
        """
        shows:
          - date: "2025-01-10"
            time: "21:00"
            timezone: "America/Chicago"
            venue: "The Dive Rift"       # venues.name
            booker: "main_booker"        # bookers.key
            lineup: ["Hella Reptilian!", "Support Band A"]
            status: "published"
            image: "show_01.jpg"
        """
        self.stdout.write("    • Seeding Shows…")

        # images_dir = base / "show_images"

        for s in shows_cfg:
            date_str = s.get("date")
            time_str = s.get("time")
            tz = s.get("timezone") or "America/Chicago"
            venue_name = s.get("venue")
            booker_key = s.get("booker")
            lineup_names = s.get("lineup") or []
            status = s.get("status") or "draft"
            # image_name = s.get("image")

            if not (date_str and time_str and venue_name):
                self.stdout.write(
                    self.style.WARNING(
                        "      (Skipping show: requires date, time, and venue.)"
                    )
                )
                continue

            try:
                d = Date.fromisoformat(date_str)
            except ValueError:
                self.stdout.write(
                    self.style.WARNING(f"      (Invalid date '{date_str}', skipping show.)")
                )
                continue

            try:
                t = Time.fromisoformat(time_str)
            except ValueError:
                self.stdout.write(
                    self.style.WARNING(f"      (Invalid time '{time_str}', skipping show.)")
                )
                continue

            venue = venue_map.get(venue_name)
            if not venue:
                self.stdout.write(
                    self.style.WARNING(
                        f"      (Show references unknown venue '{venue_name}', skipping.)"
                    )
                )
                continue

            booker = None
            if booker_key:
                booker = booker_map.get(booker_key)
                if not booker:
                    self.stdout.write(
                        self.style.WARNING(
                            f"      (Show references unknown booker key '{booker_key}', continuing without booker.)"
                        )
                    )

            # Identify show by (date, time, venue)
            show, created = Show.objects.get_or_create(
                date=d,
                time=t,
                venue=venue,
                defaults={
                    "timezone": tz,
                    "booker": booker,
                    "status": status,
                },
            )
            if not created:
                show.timezone = tz
                show.booker = booker
                show.status = status
                show.save(update_fields=["timezone", "booker", "status"])

            # M2M lineup
            if lineup_names:
                show.lineup.clear()
                for an in lineup_names:
                    act = act_map.get(an)
                    if not act:
                        self.stdout.write(
                            self.style.WARNING(
                                f"      (Show on {d} references unknown act '{an}' in lineup.)"
                            )
                        )
                        continue
                    show.lineup.add(act)

            # Attach image if provided
            # if image_name and images_dir.exists():
            #     image_path = images_dir / image_name
            #     if image_path.exists():
            #         if not show.image:
            #             with image_path.open("rb") as f:
            #                 show.image.save(image_path.name, File(f), save=True)
            #     else:
            #         self.stdout.write(
            #             self.style.WARNING(
            #                 f"      (Show image '{image_name}' not found in {images_dir}.)"
            #             )
            #         )
