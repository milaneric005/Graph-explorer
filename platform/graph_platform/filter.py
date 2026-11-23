import operator
import re
from dataclasses import dataclass
from datetime import date
from typing import Any, Callable, Dict, List

from graph_api import AttributeValue, Graph, Node


class FilterError(ValueError):
    """Baca se kada upit za filter nije ispravan ili vrednost nije odgovarajućeg tipa."""


# Komparator -> funkcija poređenja. Dvoznakovni operatori moraju biti pre
# jednoznakovnih u regularnom izrazu, da se ">=" ne bi pročitao kao ">".
COMPARATORS: Dict[str, Callable[[Any, Any], bool]] = {
    "==": operator.eq,
    "!=": operator.ne,
    ">=": operator.ge,
    "<=": operator.le,
    ">": operator.gt,
    "<": operator.lt,
}

_CONDITION_SEPARATOR = "&&"
_CONDITION_PATTERN = re.compile(r"^(?P<attribute>.+?)\s*(?P<comparator>==|!=|>=|<=|>|<)\s*(?P<value>.+)$")


@dataclass(frozen=True)
class FilterCondition:
    """Jedan uslov filtera oblika <naziv_atributa> <komparator> <vrednost_atributa>.

    Vrednost se čuva kao tekst onako kako ju je korisnik uneo; u odgovarajući
    tip (int, float, date, str) pretvara se tek prema tipu atributa u čvoru.
    """
    attribute: str
    comparator: str
    raw_value: str

    def matches(self, node: Node) -> bool:
        """Da li čvor ima atribut koji zadovoljava uslov.

        Čvor bez tog atributa ne zadovoljava uslov. Baca FilterError ako
        vrednost iz upita ne može da se pretvori u tip atributa čvora.
        """
        if self.attribute not in node.attributes:
            return False
        node_value = node.attributes[self.attribute]
        value = convert_value(self.raw_value, node_value, self.attribute)
        return COMPARATORS[self.comparator](node_value, value)


def _strip_quotes(text: str) -> str:
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "'\"":
        return text[1:-1]
    return text


def convert_value(raw_value: str, node_value: AttributeValue, attribute: str) -> AttributeValue:
    """Pretvara vrednost iz upita u tip vrednosti atributa čvora.

    - int: ceo broj (dozvoljen je i decimalan broj, npr. age > 2.5)
    - float: decimalan broj
    - date: datum u formatu YYYY-MM-DD
    - str: tekst (navodnici oko vrednosti se uklanjaju)

    Baca FilterError ako pretvaranje nije moguće.
    """
    if isinstance(node_value, str):
        return raw_value
    try:
        if isinstance(node_value, int):
            try:
                return int(raw_value)
            except ValueError:
                return float(raw_value)
        if isinstance(node_value, float):
            return float(raw_value)
        if isinstance(node_value, date):
            return date.fromisoformat(raw_value)
    except ValueError:
        pass

    expected = {int: "ceo broj (int)", float: "decimalan broj (float)",
                date: "datum u formatu YYYY-MM-DD (date)"}[type(node_value)]
    raise FilterError(
        f"Vrednost '{raw_value}' nije odgovarajućeg tipa za atribut '{attribute}': "
        f"očekuje se {expected}."
    )


def parse_filter(query: str) -> List[FilterCondition]:
    """Parsira upit za filter u listu uslova.

    Format jednog uslova je <naziv_atributa> <komparator> <vrednost_atributa>,
    gde je komparator jedan od: ==, !=, >, >=, <, <=. Više uslova se može
    spojiti sa && (svi moraju biti zadovoljeni), npr. "Age > 30 && Height >= 150".

    Baca FilterError ako upit nije u ispravnom formatu.
    """
    if query is None or not query.strip():
        raise FilterError("Upit za filter je prazan.")

    conditions = []
    for part in query.split(_CONDITION_SEPARATOR):
        part = part.strip()
        match = _CONDITION_PATTERN.match(part)
        if not match:
            raise FilterError(
                f"Neispravan uslov '{part}'. Očekivan format: <naziv_atributa> <komparator> "
                f"<vrednost_atributa>, komparator je jedan od: {', '.join(COMPARATORS)}."
            )
        attribute = _strip_quotes(match.group("attribute").strip())
        raw_value = _strip_quotes(match.group("value").strip())
        if not attribute or not raw_value:
            raise FilterError(f"Uslov '{part}' mora imati naziv atributa i vrednost.")
        conditions.append(FilterCondition(attribute, match.group("comparator"), raw_value))
    return conditions


def filter_graph(graph: Graph, query: str) -> Graph:
    """Vraća podgraf sa čvorovima koji zadovoljavaju sve uslove filtera.

    Poređenje se radi u skladu sa tipom atributa (brojevi kao brojevi,
    datumi kao datumi, stringovi leksikografski). U podgraf ulaze sve grane
    čija su oba kraja među izabranim čvorovima. Ulazni graf se ne menja, pa
    se filter može primenjivati sukcesivno na rezultat prethodne pretrage
    ili filtera.

    Baca FilterError ako upit nije ispravan ili ako vrednost nije
    odgovarajućeg tipa za atribut.
    """
    conditions = parse_filter(query)
    matching_ids = []
    for node in graph.nodes:
        # Lista (a ne generator u all()) da bi se svaki uslov proverio za svaki
        # čvor, pa se greška tipa prijavi i kada raniji uslov nije zadovoljen.
        results = [condition.matches(node) for condition in conditions]
        if all(results):
            matching_ids.append(node.node_id)
    return graph.subgraph(matching_ids)