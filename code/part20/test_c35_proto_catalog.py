from pathlib import Path

import pytest

import c35_proto_catalog as cat

FIX = Path(__file__).parent / "c35_fixtures"


@pytest.fixture(scope="module")
def services():
    return {s.full_name: s for s in cat.parse_files(FIX.glob("*.proto"))}


def test_finds_all_fixture_services(services):
    assert set(services) == {
        "nebius.common.v1.OperationService",
        "nebius.iam.v1.TokenExchangeService",
        "nebius.compute.v1.InstanceService",
        "nebius.iam.v1.ServiceAccountService",
        "nebius.iam.v1.AccessPermitService",
        "nebius.quotas.v1.QuotaAllowanceService",
    }


def test_instance_service_lro_split(services):
    s = services["nebius.compute.v1.InstanceService"]
    lro = {m.name for m in s.long_running}
    assert lro == {"Create", "Update", "Delete", "Start", "Stop"}
    reads = {m.name for m in s.methods if not m.long_running}
    assert {"Get", "GetByName", "BatchGet", "List"} <= reads


def test_multiline_rpc_with_option_body_is_parsed(services):
    s = services["nebius.compute.v1.InstanceService"]
    m = {x.name: x for x in s.methods}["ListOperationsByParent"]
    assert m.response == "common.v1.ListOperationsResponse"
    assert not m.long_running


def test_endpoint_from_api_service_name(services):
    assert services["nebius.compute.v1.InstanceService"].endpoint == "compute.api.nebius.cloud:443"
    assert services["nebius.iam.v1.TokenExchangeService"].endpoint == "tokens.iam.api.nebius.cloud:443"
    assert services["nebius.iam.v1.ServiceAccountService"].endpoint == "cpl.iam.api.nebius.cloud:443"


def test_operation_service_has_no_endpoint_and_no_lro(services):
    s = services["nebius.common.v1.OperationService"]
    assert s.endpoint == ""
    assert [m.name for m in s.methods] == ["Get", "List"]
    assert s.long_running == []


def test_comments_do_not_create_methods():
    text = '''
    package x.v1;
    service A {
      // rpc Ghost(Req) returns (Resp);
      /* rpc Ghost2(Req) returns (Resp); */
      rpc Real(Req) returns (nebius.common.v1.Operation);
    }'''
    (svc,) = cat.parse_proto(text)
    assert [m.name for m in svc.methods] == ["Real"]
    assert svc.methods[0].long_running


def test_bare_operation_only_counts_in_common_package():
    text = "package other.v1; service B { rpc X(R) returns (Operation); }"
    (svc,) = cat.parse_proto(text)
    assert not svc.methods[0].long_running


def test_streaming_flag():
    text = "package p; service S { rpc W(R) returns (stream Resp); }"
    (svc,) = cat.parse_proto(text)
    assert svc.methods[0].streaming


def test_unbalanced_block_raises():
    with pytest.raises(ValueError):
        cat.parse_proto("package p; service S { rpc A(R) returns (X);")


def test_render_marks_lro(services):
    out = cat.render([services["nebius.iam.v1.AccessPermitService"]])
    assert "LRO Create(CreateAccessPermitRequest) -> common.v1.Operation" in out
