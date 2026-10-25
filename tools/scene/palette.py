"""The illustrations' fixed light palette, taken from the hero's light theme
(sitegen/templates/hero-scene.svg). An illustration is shown through <img>, so it
cannot follow the page theme; every colour here is a literal.

Meaning, as on the hero:
  indigo  (tee)   TEEs, enclaves, attested things, the chain of evidence
  orange  (data)  the reader's data and the flow of data
  cinnabar (seal) seals and signatures only: two per picture at most (compose.py checks)
  layer hues      one or two objects per picture, for the layers a story is tagged with
"""
from .iso import Mat, mix

# neutrals
INK = "#2a2f35"
INK2 = "#5b626c"
MUTE = "#98a0aa"
SOFT = "#e6e9ed"
SOFT2 = "#cdd2d9"
PAPER = "#ffffff"
SHADOW = "#1b2433"

# plates
PLATE_TOP0, PLATE_TOP1 = "#e4e7eb", "#f4f5f7"
PLATE_L, PLATE_R, PLATE_EDGE, LIP = "#d3d8de", "#bec4cc", "#c3c9d0", "#ffffff"
TPLATE_TOP0, TPLATE_TOP1 = "#e3e5f0", "#f4f5fa"
TPLATE_L, TPLATE_R, TPLATE_EDGE = "#d0d3e8", "#b7bbd8", "#a3a9d2"

# TEE indigo
TEE, TEE2, GLOW, LED = "#3f4a8a", "#5763b4", "#6a75d6", "#7f8af0"
TEE_WASH = "#eef0fa"
TEE_RULE = "#b9bfe6"

# hardware
SUB0, SUB1, SUB2 = "#3a3f46", "#2c3036", "#22252a"
INT0, INT1, INT2 = "#646c75", "#50575f", "#41474e"
HBM0, HBM1, HBM2, HBMS = "#e1e5ea", "#bfc6ce", "#9ea6b0", "#7f8892"
DIE0, DIE1, DIEL, DIER, GRID = "#4f5a7c", "#1c2030", "#262a34", "#1a1d24", "#97a1c6"
SRV0, SRV1, SRV2, BAY = "#f3f4f6", "#3a4047", "#c7ccd3", "#9aa2ab"
PCB0, PCB1, PCB2 = "#2a6b45", "#1f5636", "#184429"
GOLD, GOLD_L, GOLD_D = "#c9a227", "#dcc061", "#a8861c"

# the reader: coat and data
DATA, DATA2, DATA_GLOW = "#df7a00", "#c2620a", "#ffc06a"
DATA_L = "#f2a54a"
LEGS, LEGS2 = "#2f6fd0", "#2457a8"
SKIN, SKIN2, HAIR, SHOE = "#e9b896", "#c98f6c", "#4a3328", "#2b2522"

# seal
SEAL, SEAL_S, SEAL2 = "#b3261e", "#7e1a15", "#e07767"

# images
SKY0, SKY1, HILL, HILL2, SUN = "#c3cedb", "#eef1f5", "#8a97a8", "#4f5a68", "#ffffff"

# layer hues (T3 to T7 on the hero): (strong, mid, light)
LAYERS = {
    "models": ("#1f5fd6", "#3f6fd0", "#d6e4fd"),
    "outputs": ("#c2255c", "#c4517a", "#fbd9e5"),
    "agents": ("#0b7f81", "#1f8e90", "#cdeeee"),
    "evaluations": ("#6d3fd6", "#7f62d9", "#e4dafc"),
    "institutions": ("#a15c07", "#b9832a", "#f6e3bd"),
}

BACKDROPS = {"white": "#ffffff", "mist": "#f3f5f7", "tee": "#f4f5fb"}

# materials (top, lit front-left, shaded front-right)
M = {
    "plate": Mat("#eceef1", PLATE_L, PLATE_R, PLATE_EDGE, "plate"),
    "tplate": Mat("#eceef6", TPLATE_L, TPLATE_R, TPLATE_EDGE, "tplate"),
    "metal": Mat(SRV0, "#dde1e6", SRV2, None, "metal"),
    "paper": Mat(PAPER, SOFT, SOFT2, None, "paper"),
    "soft": Mat(SOFT, "#d5dae0", "#bfc5cd", None, "soft"),
    "steel": Mat("#c9ced5", "#aeb5be", "#959da7", None, "steel"),
    "dark": Mat(SUB0, SUB1, SUB2, None, "dark"),
    "ink": Mat("#4a5058", "#363b42", "#262a2f", None, "ink"),
    "int": Mat(INT0, INT1, INT2, None, "int"),
    "hbm": Mat(HBM0, HBM1, HBM2, None, "hbm"),
    "die": Mat(DIE0, DIEL, DIER, None, "die"),
    "pcb": Mat(PCB0, PCB1, PCB2, None, "pcb"),
    "gold": Mat(GOLD_L, GOLD, GOLD_D, None, "gold"),
    "tee": Mat("#6a74c4", TEE2, TEE, None, "tee"),
    "teelight": Mat(TEE_WASH, "#d6d9ef", "#bcc0e0", None, "teelight"),
    "data": Mat(DATA_L, DATA, DATA2, None, "data"),
    "datalight": Mat("#fff3e2", "#fde2bf", "#f6cf9c", None, "datalight"),
    "seal": Mat("#cf3b31", SEAL, SEAL_S, None, "seal"),
    "skin": Mat(SKIN, SKIN, SKIN2, None, "skin"),
    "legs": Mat(LEGS, LEGS, LEGS2, None, "legs"),
    "hair": Mat("#5a4033", HAIR, "#3a281f", None, "hair"),
    "shoe": Mat("#3b332e", SHOE, "#1f1a17", None, "shoe"),
}
for _name, (_s, _m, _l) in LAYERS.items():
    M[_name] = Mat(mix(_m, "#ffffff", 0.28), _m, _s, None, _name)
    M[_name + "light"] = Mat(mix(_l, "#ffffff", 0.45), _l, mix(_l, _s, 0.22), None, _name + "light")


class Tint:
    """What a prop's tint resolves to: a body material for the prop's main solid, a
    solid accent material, an accent colour for marks and lamps, and a light wash."""
    __slots__ = ("name", "body", "solid", "accent", "accent2", "wash", "glow", "light")

    def __init__(self, name, body, solid, accent, accent2, wash, glow, light):
        self.name, self.body, self.solid = name, body, solid
        self.accent, self.accent2, self.wash, self.glow = accent, accent2, wash, glow
        self.light = light


TINTS = {
    "neutral": Tint("neutral", M["metal"], M["steel"], INK2, MUTE, SOFT, "#c7ccd3", M["paper"]),
    "tee": Tint("tee", M["teelight"], M["tee"], TEE2, TEE, TEE_WASH, GLOW, M["teelight"]),
    "data": Tint("data", M["datalight"], M["data"], DATA, DATA2, "#fff3e2", DATA_GLOW, M["datalight"]),
    "seal": Tint("seal", M["paper"], M["seal"], SEAL, SEAL_S, "#fbe9e7", SEAL2, M["paper"]),
    "dark": Tint("dark", M["dark"], M["ink"], LED, MUTE, SUB1, GLOW, M["int"]),
}
for _name, (_s, _m, _l) in LAYERS.items():
    TINTS[_name] = Tint(_name, M[_name + "light"], M[_name], _s, _m, _l, _m, M[_name + "light"])

TINTS["warn"] = Tint("warn", Mat("#f4e3a6", "#e2b93b", "#b8902a", None, "warn"), Mat("#ecc95a", "#e2b93b", "#b8902a", None, "warnsolid"),
                     INK, INK2, "#fbf3d6", "#f2d77a", Mat("#f4e3a6", "#e2b93b", "#b8902a", None, "warn"))
TINT_NAMES = list(TINTS)

# connector colours: (stroke, glow). Cinnabar is for seals, never a link.
LINK_COLORS = {
    "data": (DATA, DATA_GLOW),
    "tee": (TEE2, GLOW),
    "ink": (INK2, None),
    "mute": (MUTE, None),
}
for _name, (_s, _m, _l) in LAYERS.items():
    LINK_COLORS[_name] = (_s, None)

# the props that may wear the cinnabar tint (everything else marks a seal by a parameter)
SEAL_PROPS = ("seal", "stamp", "certificate")
