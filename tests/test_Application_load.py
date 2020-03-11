import pytest
import yaml

from tloen.domain import Application


@pytest.mark.asyncio
async def test(tmp_path, serialization_application):
    app_one = serialization_application
    file_path = tmp_path / "application.yaml"
    assert not file_path.exists()
    app_one.save(file_path)
    assert file_path.exists()
    app_two = await Application.load(file_path)
    assert app_one is not app_two
    assert yaml.dump(app_one.serialize()) == yaml.dump(app_two.serialize())
