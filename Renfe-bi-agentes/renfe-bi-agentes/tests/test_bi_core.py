"""Tests de la lógica analítica y de la coherencia de los datos reales."""
import pytest

from mcp_server import bi_core as c


def test_todas_las_tablas_cargan():
    assert c.estado_datos()["ok"]


def test_todas_las_filas_tienen_fuente_existente():
    ids = {f["fuente_id"] for f in c.fuentes()}
    for t in c.TABLAS:
        if t == "fuentes":
            continue
        for fila in c.cargar(t):
            assert fila["fuente_id"] in ids, (t, fila)


def test_suma_trimestral_2025_cuadra_con_anual():
    total = {r["periodo"]: r["viajeros_millones"] for r in c.serie_viajeros("TOTAL")}
    suma = sum(total[p] for p in ("2025T1", "2025T2", "2025T3", "2025T4"))
    anual = next(r for r in c.cargar("viajeros_anual") if r["corredor_id"] == "TOTAL")["viajeros_millones"]
    assert abs(suma - anual) / anual < 0.01


def test_cuotas_no_superan_100():
    from collections import defaultdict
    acc = defaultdict(float)
    for r in c.cuotas_mercado():
        acc[(r["periodo"], r["corredor_id"])] += r["cuota_pct"]
    assert all(v <= 100 for v in acc.values())


def test_mercado_bcn_es_el_mayor():
    tabla = c.comparar_corredores()
    assert max(tabla, key=lambda r: r["mercado_estimado_2025_MEUR"])["corredor_id"] == "BCN"


def test_elasticidades_bcn_inelastica_sur_elastica():
    assert c.elasticidad_precio("BCN")["resumen"]["clase"] == "inelastica"
    assert c.elasticidad_precio("SEV")["resumen"]["clase"] == "elastica"


def test_observacion_mismo_signo_no_interpretable():
    vlc = c.elasticidad_precio("VLC")["observaciones"]
    assert any(not o["interpretable"] for o in vlc)


def test_simulacion_coherente():
    s = c.simular_escenario_precio("BCN", 5)
    esc = s["escenarios"]
    assert esc["optimista"]["var_ingresos_pct"] >= esc["central"]["var_ingresos_pct"] >= esc["pesimista"]["var_ingresos_pct"]
    assert s["escenarios"]["central"]["var_viajeros_pct"] < 0
    s0 = c.simular_escenario_precio("SEV", 0)
    assert s0["escenarios"]["central"]["var_ingresos_pct"] == 0


def test_simulacion_con_elasticidad_usuario():
    s = c.simular_escenario_precio("ALI", -10, elasticidad=-1.0)
    assert list(s["escenarios"]) == ["central"]
    assert s["escenarios"]["central"]["var_ingresos_pct"] == pytest.approx(0.0, abs=0.1)


@pytest.mark.parametrize("cid,accion", [
    ("BCN", "PREMIUM CON DEFENSA SELECTIVA"),
    ("SEV", "RECUPERAR DEMANDA"),
    ("MAL", "RECUPERAR DEMANDA"),
    ("VLC", "MANTENER Y VIGILAR"),
])
def test_recomendaciones(cid, accion):
    assert c.recomendar_accion(cid)["accion"] == accion


def test_corredor_invalido():
    with pytest.raises(c.DatoNoDisponible):
        c.kpis_corredor("XXX")
    with pytest.raises(c.DatoNoDisponible):
        c.simular_escenario_precio("BCN", 80)
