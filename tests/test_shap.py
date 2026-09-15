from services.xai.shap_explainer import explain_risk


def test_shap_explanation():

    result = explain_risk(
        kyc_risk=0.70,
        aml_risk=0.91
    )

    assert len(result) == 2

    feature_names = {
        item["feature"]
        for item in result
    }

    assert "kyc_risk" in feature_names
    assert "aml_risk" in feature_names

    for item in result:
        assert isinstance(item["importance"], float)