"""
MedFlow demonstration hospital network.

PUBLIC  = facts retrieved from public sources on 2026-10-31 (see SOURCES).
SIM     = SIMULATED operational profile. Not the hospital's real capability,
          capacity, staffing or response behaviour. Demo values only.
Real hospital names are used only as demonstration network references, not as
claims of partnership, and never as live bed availability.
"""

RETRIEVED = "2026-10-31"

EQUIPMENT_TYPES = [
    # code, name, category, description
    ("EQ_CONV_VENTILATOR", "Conventional neonatal ventilator", "EQUIPMENT", "Invasive conventional mechanical ventilation"),
    ("EQ_HFOV", "High-frequency oscillatory ventilator", "EQUIPMENT", "Rescue high-frequency ventilation"),
    ("EQ_CPAP", "Neonatal CPAP driver", "EQUIPMENT", "Continuous positive airway pressure"),
    ("EQ_HFNC", "Heated humidified high-flow system", "EQUIPMENT", "High-flow nasal cannula therapy"),
    ("EQ_INO", "Inhaled nitric oxide delivery system", "EQUIPMENT", "Pulmonary vasodilator therapy for PPHN"),
    ("EQ_THERAPEUTIC_COOLING", "Servo-controlled cooling device", "EQUIPMENT", "Therapeutic hypothermia for HIE"),
    ("EQ_AEEG", "Amplitude-integrated / continuous EEG", "EQUIPMENT", "Continuous brain function monitoring"),
    ("EQ_NEONATAL_ECHO", "Neonatal echocardiography machine", "EQUIPMENT", "Bedside cardiac ultrasound"),
    ("EQ_ROP_LASER", "Retinal laser photocoagulation unit", "EQUIPMENT", "Treatment of retinopathy of prematurity"),
    ("EQ_INTENSIVE_PHOTOTHERAPY", "Intensive (double-surface) phototherapy", "EQUIPMENT", "High-irradiance phototherapy"),
    ("EQ_PERITONEAL_DIALYSIS", "Neonatal peritoneal dialysis set-up", "EQUIPMENT", "Renal replacement / ammonia removal"),
    ("EQ_CRANIAL_USG", "Cranial ultrasound", "EQUIPMENT", "Bedside head ultrasound"),
    ("EQ_TRANSPORT_INCUBATOR", "Transport incubator", "EQUIPMENT", "Neonatal transport"),
    ("FAC_NEONATAL_SURGICAL_OT", "Neonatal surgical theatre", "FACILITY", "Operating theatre equipped for neonates"),
    ("FAC_PAED_CATH_LAB", "Paediatric cardiac catheterisation lab", "FACILITY", "Interventional cardiology for neonates"),
    ("FAC_BLOOD_BANK", "On-site blood bank", "FACILITY", "Blood products incl. exchange transfusion"),
    ("FAC_HUMAN_MILK_BANK", "Human milk bank", "FACILITY", "Donor human milk"),
    ("FAC_ISOLATION_ROOM", "Neonatal isolation room", "FACILITY", "Isolation for resistant infections"),
    ("FAC_NICU_PROCEDURE_ROOM", "NICU procedure room", "FACILITY", "Bedside procedures under sedation/anaesthesia"),
    ("FAC_MRI", "MRI with neonatal protocol", "FACILITY", "Neonatal brain MRI"),
    ("FAC_PARENTERAL_NUTRITION", "Parenteral nutrition pharmacy", "FACILITY", "Compounded intravenous nutrition"),
    ("FAC_CONTRAST_RADIOLOGY", "Paediatric contrast radiology", "FACILITY", "Upper GI / contrast enema studies"),
]

SPECIALIST_TYPES = [
    ("SP_NEONATOLOGIST", "Neonatologist", "Neonatal intensive care consultant"),
    ("SP_PAED_SURGEON", "Paediatric surgeon", "Neonatal and paediatric general surgery"),
    ("SP_PAED_CARDIOLOGIST", "Paediatric cardiologist", "Echocardiography and interventional cardiology"),
    ("SP_PAED_CARDIAC_SURGEON", "Paediatric cardiac surgeon", "Congenital heart surgery"),
    ("SP_PAED_NEUROLOGIST", "Paediatric neurologist", "Neonatal seizures, EEG interpretation"),
    ("SP_PAED_NEUROSURGEON", "Paediatric neurosurgeon", "CSF diversion and neonatal neurosurgery"),
    ("SP_PAED_OPHTHALMOLOGIST", "Paediatric ophthalmologist (ROP)", "Retinopathy of prematurity treatment"),
    ("SP_PAED_ANAESTHETIST", "Paediatric anaesthetist", "Neonatal anaesthesia"),
    ("SP_PAED_PULMONOLOGIST", "Paediatric pulmonologist", "Chronic lung disease management"),
    ("SP_PAED_NEPHROLOGIST", "Paediatric nephrologist", "Neonatal renal replacement therapy"),
    ("SP_METABOLIC_GENETICIST", "Metabolic / genetics specialist", "Inborn errors of metabolism"),
]

ALL_EQ = [e[0] for e in EQUIPMENT_TYPES]

HOSPITALS = [
    {
        "id": "HOSP001", "short_name": "Demo Referral Centre", "is_fictional": True,
        "public": {
            "name": "MedFlow Demo Referral Centre (fictional)",
            "locality": "Hosur Road, near Electronic City, Bengaluru (fictional site)",
            "address": None, "latitude": 12.861500, "longitude": 77.653000,
            "coordinate_quality": "FICTIONAL",
        },
        "network": {"is_active": True, "can_refer": True, "can_receive": False},
        "sim": {
            "nicu_level": 2, "readiness": 0.70,
            "equipment": ["EQ_CPAP", "EQ_HFNC", "EQ_CONV_VENTILATOR", "EQ_INTENSIVE_PHOTOTHERAPY",
                          "EQ_CRANIAL_USG", "EQ_TRANSPORT_INCUBATOR"],
            "unavailable_equipment": {},
            "specialists": ["SP_NEONATOLOGIST"],
            "capacity": {"NICU_HDU": (12, 9)},
        },
    },
    {
        "id": "HOSP002", "short_name": "Rainbow Electronic City", "is_fictional": False,
        "public": {
            "name": "Rainbow Children's Hospital, Electronic City",
            "locality": "Electronic City, Bengaluru",
            "address": None, "latitude": 12.845200, "longitude": 77.660200,
            "coordinate_quality": "APPROXIMATE_LOCALITY",
        },
        "network": {"is_active": True, "can_refer": False, "can_receive": True},
        "sim": {
            "nicu_level": 3, "readiness": 0.85,
            "equipment": ["EQ_CONV_VENTILATOR", "EQ_HFOV", "EQ_CPAP", "EQ_HFNC", "EQ_INO",
                          "EQ_THERAPEUTIC_COOLING", "EQ_AEEG", "EQ_NEONATAL_ECHO", "EQ_ROP_LASER",
                          "EQ_INTENSIVE_PHOTOTHERAPY", "EQ_CRANIAL_USG", "EQ_TRANSPORT_INCUBATOR",
                          "FAC_NICU_PROCEDURE_ROOM", "FAC_BLOOD_BANK", "FAC_HUMAN_MILK_BANK",
                          "FAC_ISOLATION_ROOM", "FAC_MRI", "FAC_PARENTERAL_NUTRITION"],
            "unavailable_equipment": {},
            "specialists": ["SP_NEONATOLOGIST", "SP_PAED_OPHTHALMOLOGIST", "SP_PAED_ANAESTHETIST",
                            "SP_PAED_PULMONOLOGIST", "SP_PAED_NEUROLOGIST", "SP_PAED_CARDIOLOGIST"],
            # 10 beds, 9 occupied -> exactly 1 free; the demo consumes it before confirmation
            "capacity": {"NICU_INTENSIVE": (10, 9), "NICU_HDU": (8, 6)},
        },
    },
    {
        "id": "HOSP003", "short_name": "Chinmaya Mission", "is_fictional": False,
        "public": {
            "name": "Chinmaya Mission Hospital",
            "locality": "Indiranagar, Bengaluru",
            "address": "1/1, Chinmaya Mission Hospital Rd, Opp. Krishna Temple, Defence Colony, Indiranagar, Bengaluru 560038",
            "latitude": 12.974500, "longitude": 77.641000,
            "coordinate_quality": "APPROXIMATE_LOCALITY",
        },
        "network": {"is_active": True, "can_refer": False, "can_receive": True},
        "sim": {
            "nicu_level": 3, "readiness": 0.80,
            "equipment": ["EQ_CONV_VENTILATOR", "EQ_CPAP", "EQ_HFNC", "EQ_ROP_LASER", "EQ_AEEG",
                          "EQ_INTENSIVE_PHOTOTHERAPY", "EQ_CRANIAL_USG", "EQ_NEONATAL_ECHO",
                          "FAC_NICU_PROCEDURE_ROOM", "FAC_BLOOD_BANK", "FAC_MRI", "FAC_PARENTERAL_NUTRITION"],
            "unavailable_equipment": {},
            "specialists": ["SP_NEONATOLOGIST", "SP_PAED_OPHTHALMOLOGIST", "SP_PAED_ANAESTHETIST",
                            "SP_PAED_NEUROLOGIST"],
            "capacity": {"NICU_INTENSIVE": (8, 5), "NICU_HDU": (6, 4)},
        },
    },
    {
        "id": "HOSP004", "short_name": "KIMS", "is_fictional": False,
        "public": {
            "name": "Kempegowda Institute of Medical Sciences Hospital (KIMS)",
            "locality": "V.V. Puram, Bengaluru",
            "address": None, "latitude": 12.956500, "longitude": 77.574278,
            "coordinate_quality": "SOURCED",
        },
        "network": {"is_active": True, "can_refer": False, "can_receive": True},
        "sim": {
            "nicu_level": 4, "readiness": 0.70,
            "equipment": ["EQ_CONV_VENTILATOR", "EQ_HFOV", "EQ_CPAP", "EQ_HFNC", "EQ_INO",
                          "EQ_THERAPEUTIC_COOLING", "EQ_AEEG", "EQ_NEONATAL_ECHO", "EQ_ROP_LASER",
                          "EQ_INTENSIVE_PHOTOTHERAPY", "EQ_PERITONEAL_DIALYSIS", "EQ_CRANIAL_USG",
                          "FAC_NEONATAL_SURGICAL_OT", "FAC_BLOOD_BANK", "FAC_MRI", "FAC_PARENTERAL_NUTRITION",
                          "FAC_CONTRAST_RADIOLOGY", "FAC_ISOLATION_ROOM", "FAC_NICU_PROCEDURE_ROOM"],
            "unavailable_equipment": {"EQ_ROP_LASER": "SIMULATED: out of service for maintenance"},
            "specialists": ["SP_NEONATOLOGIST", "SP_PAED_SURGEON", "SP_PAED_NEUROSURGEON",
                            "SP_PAED_ANAESTHETIST", "SP_PAED_OPHTHALMOLOGIST", "SP_PAED_NEUROLOGIST",
                            "SP_PAED_NEPHROLOGIST", "SP_PAED_PULMONOLOGIST"],
            "capacity": {"NICU_INTENSIVE": (14, 11), "NICU_SURGICAL": (6, 4), "NICU_HDU": (10, 7)},
        },
    },
    {
        "id": "HOSP005", "short_name": "Bangalore Baptist", "is_fictional": False,
        "public": {
            "name": "Bangalore Baptist Hospital",
            "locality": "Hebbal, Bengaluru",
            "address": None, "latitude": 13.038266, "longitude": 77.589270,
            "coordinate_quality": "SOURCED",
        },
        "network": {"is_active": True, "can_refer": False, "can_receive": True},
        "sim": {
            "nicu_level": 3, "readiness": 0.88,
            "equipment": ["EQ_CONV_VENTILATOR", "EQ_HFOV", "EQ_CPAP", "EQ_HFNC", "EQ_INO",
                          "EQ_THERAPEUTIC_COOLING", "EQ_AEEG", "EQ_NEONATAL_ECHO", "EQ_ROP_LASER",
                          "EQ_INTENSIVE_PHOTOTHERAPY", "EQ_CRANIAL_USG", "EQ_TRANSPORT_INCUBATOR",
                          "FAC_NICU_PROCEDURE_ROOM", "FAC_BLOOD_BANK", "FAC_HUMAN_MILK_BANK",
                          "FAC_MRI", "FAC_PARENTERAL_NUTRITION", "FAC_ISOLATION_ROOM"],
            "unavailable_equipment": {},
            "specialists": ["SP_NEONATOLOGIST", "SP_PAED_OPHTHALMOLOGIST", "SP_PAED_ANAESTHETIST",
                            "SP_PAED_NEUROLOGIST", "SP_PAED_PULMONOLOGIST"],
            "capacity": {"NICU_INTENSIVE": (12, 8), "NICU_HDU": (10, 7)},
        },
    },
    {
        "id": "HOSP006", "short_name": "Manipal Hebbal", "is_fictional": False,
        "public": {
            "name": "Manipal Hospital, Hebbal",
            "locality": "Hebbal, Bengaluru",
            "address": "Kirloskar Business Park, Bellary Road, Hebbal, Bangalore 560024",
            "latitude": 13.044600, "longitude": 77.595800,
            "coordinate_quality": "APPROXIMATE_LOCALITY",
        },
        "network": {"is_active": True, "can_refer": False, "can_receive": True},
        "sim": {
            "nicu_level": 3, "readiness": 0.82,
            "equipment": ["EQ_CONV_VENTILATOR", "EQ_HFOV", "EQ_CPAP", "EQ_HFNC", "EQ_INO",
                          "EQ_THERAPEUTIC_COOLING", "EQ_AEEG", "EQ_NEONATAL_ECHO", "EQ_ROP_LASER",
                          "EQ_INTENSIVE_PHOTOTHERAPY", "EQ_CRANIAL_USG",
                          "FAC_NICU_PROCEDURE_ROOM", "FAC_BLOOD_BANK", "FAC_MRI",
                          "FAC_PARENTERAL_NUTRITION", "FAC_ISOLATION_ROOM"],
            "unavailable_equipment": {},
            # SIMULATED: no paediatric ophthalmologist in this demo profile
            "specialists": ["SP_NEONATOLOGIST", "SP_PAED_ANAESTHETIST", "SP_PAED_NEUROLOGIST",
                            "SP_PAED_PULMONOLOGIST", "SP_PAED_CARDIOLOGIST"],
            "capacity": {"NICU_INTENSIVE": (10, 7), "NICU_HDU": (8, 5)},
        },
    },
    {
        "id": "HOSP007", "short_name": "Aster CMI", "is_fictional": False,
        "public": {
            "name": "Aster CMI Hospital",
            "locality": "Sahakar Nagar, Hebbal, Bengaluru",
            "address": "No. 43/2, New Airport Road, NH 44, Sahakar Nagar, Hebbal, Karnataka 560092",
            "latitude": 13.056600, "longitude": 77.592400,
            "coordinate_quality": "APPROXIMATE_LOCALITY",
        },
        "network": {"is_active": True, "can_refer": False, "can_receive": True},
        "sim": {
            "nicu_level": 4, "readiness": 0.90,
            "equipment": ALL_EQ,
            "unavailable_equipment": {},
            "specialists": [s[0] for s in SPECIALIST_TYPES],
            # SIMULATED: intensive beds full; cardiac and surgical beds free
            "capacity": {"NICU_INTENSIVE": (16, 16), "NICU_CARDIAC": (6, 4),
                         "NICU_SURGICAL": (8, 6), "NICU_HDU": (10, 8)},
        },
    },
    {
        "id": "HOSP008", "short_name": "St. Martha's", "is_fictional": False,
        "public": {
            "name": "St. Martha's Hospital",
            "locality": "Nrupathunga Road, Bengaluru",
            "address": None, "latitude": 12.971940, "longitude": 77.593690,
            "coordinate_quality": "PROXY_SOURCED",
        },
        "network": {"is_active": True, "can_refer": False, "can_receive": True},
        "sim": {
            "nicu_level": 2, "readiness": 0.75,
            "equipment": ["EQ_CPAP", "EQ_HFNC", "EQ_INTENSIVE_PHOTOTHERAPY", "EQ_CRANIAL_USG",
                          "EQ_AEEG", "FAC_BLOOD_BANK", "FAC_MRI"],
            "unavailable_equipment": {},
            "specialists": ["SP_NEONATOLOGIST", "SP_PAED_NEUROLOGIST"],
            "capacity": {"NICU_HDU": (10, 6)},
        },
    },
]

SOURCES = {
    "HOSP001": {"note": "Fictional demonstration referral centre. No real-world counterpart.", "sources": []},
    "HOSP002": {
        "verified": ["Rainbow Children's Medicare launched a 90-bed facility in Electronic City, Bengaluru (report updated 28 Jan 2026)"],
        "not_verified": ["street address", "exact coordinates (locality-level approximation used)", "any NICU capability"],
        "sources": ["https://scanx.trade/stock-market-news/stocks/rainbow-children-s-medicare-expands-in-bengaluru-with-new-90-bed-facility-in-electronic-city/31124788"],
    },
    "HOSP003": {
        "verified": ["name", "street address (Indiranagar 560038)"],
        "not_verified": ["exact coordinates (locality-level approximation used)", "any NICU capability; source page does not mention a NICU"],
        "sources": ["https://www.chinmayamission.com/global/chinmaya-mission-hospital"],
    },
    "HOSP004": {
        "verified": ["name", "hospital on the V.V. Puram campus", "coordinates 12.9565 N, 77.574278 E (Wikipedia, for the institute)"],
        "not_verified": ["street address", "any NICU capability"],
        "ambiguity": "'KIMS Bengaluru' interpreted as Kempegowda Institute of Medical Sciences, not KIMS Hospitals (Krishna Institute). Confirm with the project owner.",
        "sources": ["https://en.wikipedia.org/wiki/Kempegowda_Institute_of_Medical_Sciences"],
    },
    "HOSP005": {
        "verified": ["name", "locality Hebbal", "coordinates 13.038266 N, 77.589270 E (Wikipedia)", "formally opened 15 Jan 1973"],
        "not_verified": ["street address", "any NICU capability; source page does not mention one"],
        "sources": ["https://en.wikipedia.org/wiki/Bangalore_Baptist_Hospital"],
    },
    "HOSP006": {
        "verified": ["name", "address Kirloskar Business Park, Bellary Road, Hebbal 560024"],
        "not_verified": ["exact coordinates (locality-level approximation used)", "any NICU capability; source page does not mention one"],
        "sources": ["https://www.manipalhospitalsglobal.com/hospitals/hebbal"],
    },
    "HOSP007": {
        "verified": ["name", "address No. 43/2, New Airport Road, NH 44, Sahakar Nagar, Hebbal 560092", "a 'Paediatrics & Neonatology' specialty is listed"],
        "not_verified": ["exact coordinates (locality-level approximation used)", "NICU level, beds or equipment"],
        "sources": ["https://www.asterhospitals.in/hospitals/aster-cmi-bangalore"],
    },
    "HOSP008": {
        "verified": ["name", "co-located St. Martha's College of Nursing coordinates 12.97194 N, 77.59369 E (ROR) used as a proxy"],
        "not_verified": ["street address", "hospital's own coordinates", "any NICU capability"],
        "sources": ["https://api.ror.org/v2/organizations/https://ror.org/040eytj64"],
    },
}
