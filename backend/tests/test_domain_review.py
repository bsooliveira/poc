from test_workflow import generated_event


def test_human_can_correct_domain_without_approving(client):
    event = generated_event(client)
    item = event["result"]["items"][0]
    payload = {
        k: item[k]
        for k in (
            "question_pt",
            "answer_pt",
            "question_en",
            "answer_en",
            "source_chunk_ids",
        )
    }
    payload.update(
        expected_version=event["version"],
        domain="Agenda corrigida",
        reviewed=False,
        review_note="Correção sintética de domínio",
    )
    response = client.patch(
        f"/api/events/{event['id']}/items/{item['id']}", json=payload
    )
    assert response.status_code == 200, response.text
    updated = response.json()["result"]["items"][0]
    assert updated["domain"] == "Agenda corrigida"
    assert updated["human_edited"] and not updated["reviewed"]
    assert updated["requires_human_review"]
