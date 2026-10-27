import numpy as np
import pytest
from src.kinematics import PRESETS, DHValidationError, calculate, dh_matrix, validated_rows


def test_dh_identity_and_pure_transform():
    assert np.allclose(dh_matrix(0,0,0,0), np.eye(4))
    assert np.allclose(dh_matrix(90,.3,2,0), np.array([
        [0,-1,0,0],[1,0,0,2],[0,0,1,.3],[0,0,0,1]]),atol=1e-12)


def test_rrr_analytic_position():
    result=calculate(PRESETS['rrr'])
    t1,t2,t3=np.deg2rad([45,30,45]); radius=.6*np.cos(t2)+.4*np.cos(t2+t3)
    expect=[radius*np.cos(t1), radius*np.sin(t1), .2+.6*np.sin(t2)+.4*np.sin(t2+t3)]
    assert np.allclose(result['end_effector'],expect,atol=1e-12)
    assert result['configuration']=='RRR'
    assert result['active_units']==['deg']*3


@pytest.mark.parametrize('preset', ['rrr','rrp','rpp','ppp'])
def test_presets_calculate(preset):
    value=calculate(PRESETS[preset])
    assert value['configuration']==preset.upper()
    assert len(value['frames'])==4
    assert len(value['links'])==3
    assert value['orthogonality_error']<1e-12
    assert value['rotation_determinant']==pytest.approx(1,abs=1e-12)
    assert np.allclose(np.array(value['T_final'])[:3,3],value['end_effector'])


def test_prismatic_displacement_along_preceding_z():
    for config in ['rrp','rpp','ppp']:
        for j, item in enumerate(PRESETS[config]):
            if item['type']!='P':continue
            a=[dict(p) for p in PRESETS[config]]
            b=[dict(p) for p in PRESETS[config]]
            b[j]['d']+=.25
            r0=calculate(a);r1=calculate(b)
            delta=np.array(r1['end_effector'])-np.array(r0['end_effector'])
            axis=np.array(r0['links'][j]['axis_z'])
            assert np.allclose(delta,.25*axis,atol=1e-12), (config,j)
            assert np.linalg.norm(delta)==pytest.approx(.25,abs=1e-12)


def test_revolute_theta_and_fixed_d():
    rows=[dict(r) for r in PRESETS['rrp']]
    original=calculate(rows)
    rows[0]['theta']+=15
    changed=calculate(rows)
    assert not np.allclose(original['end_effector'],changed['end_effector'])
    # Uma junta P admite theta fixo não nulo e ainda assim d é sua coordenada ativa.
    assert original['links'][2]['active_parameter']=='d'


def test_ppp_orthogonal_axes_and_linear_motion():
    data=calculate(PRESETS['ppp'])
    directions=np.array([r['axis_z'] for r in data['links']]).T
    assert np.allclose(directions.T@directions,np.eye(3),atol=1e-12)
    assert np.allclose(np.abs(directions).sum(axis=0),[1,1,1])
    assert data['active_coordinates']==pytest.approx([.4,.4,.4])


def test_validation_bad_type_and_infinite():
    rows=[dict(p) for p in PRESETS['rrr']]
    for bad in ('S','X',None):
        arr=[dict(p) for p in rows];arr[0]['type']=bad
        with pytest.raises(DHValidationError):validated_rows(arr)
    for invalid in ([],[{}, {}, {}],[{'theta':float('nan'),'d':0,'a':0,'alpha':0}]*3,
                    [{'type':'P','theta':0,'d':6,'a':0,'alpha':0}]*3):
        with pytest.raises(DHValidationError):validated_rows(invalid)


def test_legacy_v1_rows_are_rrr():
    original=[{k:val for k,val in item.items() if k!='type'} for item in PRESETS['rrr']]
    assert calculate(original)['configuration']=='RRR'


def test_rotation_matrices_random():
    rng=np.random.default_rng(2026)
    for _ in range(50):
        config=rng.choice(['R','P'],3)
        rows=[{'type':k,'theta':rng.uniform(-180,180),'d':rng.uniform(-1,1),
               'a':rng.uniform(-1,1),'alpha':rng.uniform(-180,180)} for k in config]
        result=calculate(rows)
        R=np.array(result['T_final'])[:3,:3]
        assert np.allclose(R.T@R,np.eye(3),atol=1e-12)
