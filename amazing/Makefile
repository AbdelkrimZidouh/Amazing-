run:
	@python3 a_maze_ing.py config.txt

install:
	pip3 install -r requirements.txt


debug:
	@python3 -m pdb a_maze_ing.py config.txt

clean:
	@find -name "__pycache__" -exec rm -rf {} +
	@rm -rf .mypy_cache

package:
	python3 -m build
	mv dist/* .
	rm -rf dist

lint:
	python3 -m flake8 mazegen/* utils/* a_maze_ing.py
	python3 -m  mypy . \
		--warn-return-any \
		--warn-unused-ignores \
		--ignore-missing-imports \
		--disallow-untyped-defs \
		--check-untyped-defs

