# Dance of the Solos
A Python/d3.js implementation of the solo calculus and of solo diagrams.  
This forms the submission for CM30082 Dissertation, MComp Comp.Sci. w/ Maths. for Adam Lassiter, University of Bath, GB, 2017-18.

## Prerequisites
The following do not represent minimum requirements, but those used in production and testing.
* Python 3.7
    * Multiset >= v2.0.0
    * regex >= 2018.2.8
    * flask >= 0.12.0
        * flask_restful >= 0.3.6
        * flask_cors >= 3.0.3
* Webbrowser
    * d3.js >= 4.13
    * jQuery >= 3.3.1

## Getting Started
The project can be run from the [src/](src) directory without any need for compiling/building.
Currently the system exists in three major parts.

### Calculus
Found under the [calculus/](/src/calculus) directory, this provides an implementation of the solo calculus, as well as an interface to interact with.  
Executing the [tests.py](/src/calculus/tests.py) file runs all available unit tests, while the [calculus.py](src/calculus/calculus.py) file provides a REPL interface.

### Diagrams
Found under the [diagrams/](/src/diagrams) directory, this provides an implementation only of solo diagrams.  
Executing the [tests.py](/src/diagrams/tests.py) file runs all available unit tests.  
Executing the [rest.py](/src/diagrams/rest.py) file starts a Flask server on localhost:8001 to be used by the visualisation.

### Visualisation
Found under the [visualisation/](/src/visualisation) directory, this provides a visualisation only of solo diagrams, with a symlinked data file [graph.json](/src/diagrams/graph.json).  
Running a web-server on [index.html](/src/visualisation/index.html) will produce an interactive output within a web-browser pointed at the server page (by default, this is on localhost:8000).  
For this to function, there must be an instance of [rest.py](/src/diagrams/rest.py) running locally to the server as a Flask server

## Contributing
See [CONTRIBUTING.md](CONTRIBUTING.md) for details on code of conduct and the process for submitting pull requests.

## Authors
This project remains the sole work of Adam Lassiter (https://github.com/AdamLassiter) (http://people.bath.ac.uk/atl35/ - see [COPYRIGHT.md](COPYRIGHT.md) for details.

## License
This project is licensed under the MIT License - see [LICENSE.md](LICENSE.md) for details.

## Acknowledgements
* Prof. Guy McCusker - Project Supervisor
