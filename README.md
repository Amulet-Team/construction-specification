# Construction File Format Specification

The construction format specification aims to allow third-party world editors to support a version flexible way of 
importing and exporting various parts of Minecraft worlds. 

## Repository Contents

This repository contains the following information for those wishing to integrate construction file support into their
programs:

### Specifications
In the `/specifications/` directory, each version and the associated format information of the construction 
specification is outline in each version's markdown file following the conventions `version_{version number}.md`

Current Specification Versions:
 - [Version 0](https://github.com/Podshot/construction-specification/blob/master/specifications/version_0.md)

### Format Libraries
Libraries for loading and saving construction files are provided in this repository for use in other third-party programs
as well as for reference for those who wish to write their own libraries. Each of these can be found in a directory
with the name of the programming language the library was written in. Multiple libraries for the same language may be present.

The following languages are currently present or being worked on:
- python
  - Requires the following python modules 
    - [numpy](https://numpy.org/)
    - [Amulet-Core](https://github.com/Amulet-Team/Amulet-Core)
  - Currently tested with Python 3.6+
- Java (work in progress)
  - Requires the java NBT library from Github user [Querz](https://github.com/Querz/NBT), however any NBT library could 
    be used as long as it supports loading of gzip'd TAG_Compound's from a ByteBuffer or array of `bytes`
    
Feel free to open a pull request with changes to existing libraries or create a library for a new language and 
we'll accept them!

***Note: In order for your library to be accepted, you must provide and license it under the MIT License***

## Contributing
Contributions to this repository are always welcomed. There is a loose system in place in order for us to properly
manage contributions to this repository.

### RFCs
Issues marked as `[RFC]` (or have the `rfc` label) are issues that hold discussions on how a change to the format might
impact libraries and those who use said libraries as well opportunities to discuss how to improve a format change that will
be added in a future revision. RFCs may be postponed if the discussion warrants additional time to give more consideration.
RFCs may also be closed if it is determined that the the feature or change is deemed unsatisfactory or will have greater
consequences than we have the resources to fix.

### Proposals
Issues marked as `[Proposal]` (or have the `proposal` label) are issues that are for work in progress ideas for features or changes to the file format that improve the format/system overall. These are meant for getting different ideas from the community on how to approach the given feature/change and may be rejected if they are deemed too complex or outside the goals of the specification.

### Important Notes
**All pull requests, issues, additions and changes submitted to this repository are licensed under the MIT License. Any
code contributed must abide by the license and also be under the same license**



