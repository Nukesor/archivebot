default: venv

venv:
	python3 -m venv venv
	venv/bin/pip install --upgrade pip
	venv/bin/pip install -r requirements.txt --upgrade
	venv/bin/pip install -r requirements-dev.txt --upgrade

tesclean:
	rm -rf venv
