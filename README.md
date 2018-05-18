# Introduction

This repository contains code for running a small system to work with oncology data, 
including DICOM images. It consists of the following components:

* [Orthanc DICOM server](http://book.orthanc-server.com/): for storing DICOM images
* [Mongo database](https://docs.mongodb.com/#using-mongodb): for storing extracted information
* Data warehouse: code for extracting information from DICOM and other sources
* Data science: code for training machine learning/statistical models


# Install docker and start containers

Start by installing [docker](https://docs.docker.com/engine/installation/#desktop) and
`docker-compose`. You can learn more about each of these using:

```
docker --help
docker-compose --help
```

Next, you can start up the containers with the following command:

```
docker-compose up
```

This command reads the container architecture specified in
 `docker-compose.yml`,
builds the containers and connections between them, and starts them up. Note that
this can take a little while the first time you run it because it
has to download and install a fair amount of software. To stop
the containers hit `Ctrl-C`. The next time you start them up will
be quicker.


# Download DICOM images and clinical data

* Download the [data set [554.8 MB]](https://s3.amazonaws.com/oncora-data-science-challenge/data.zip), which
includes clinical data from [head and neck cancer patients](https://wiki.cancerimagingarchive.net/display/Public/TCGA-HNSC#57f54e90dc314214821e6a99606a0db1) and DICOM files for three of those patients. 

* Unzip the files in the `data_warehouse/` directory.

* Import the DICOM files into server: `docker-compose run --rm data_warehouse python import_dicom_files.py dicom 8042 dicom/`

* Read through the [Orthanc](http://book.orthanc-server.com/) documentation for a concise introduction to the DICOM standard and protocol.

* Explore the DICOM files using Orthanc web UI: `http://localhost:8042/app/explorer.html`

* Take a look at the [DICOM standard](https://dicom.innolitics.com/ciods): especially
[RT Dose](https://dicom.innolitics.com/ciods/rt-dose), 
[RT Structure Set](https://dicom.innolitics.com/ciods/rt-structure-set), and 
[RT Plan](https://dicom.innolitics.com/ciods/rt-plan). 

You can remove the DICOM files from the server by running `clear_dicom.py`.

# Extracting data from DICOM files

Look through the script `data_warehouse/extract_data_examples.py` 
and run it using the following command:

```
docker-compose run --rm data_warehouse python extract_data_examples.py
```

This script has examples of how to get information from the DICOM 
server and how to store it in the database.

Mongo can store multiple databases, each of which consists of multiple collections
of documents. The default database is specified in `docker-compose.yml` and each
of the documents created in `extract_data_examples.py` is inserted into an
`examples` collection. 

After running the script you can inspect the database 
by running `mongo` from the command line. Note that you may need to [install the mongo shell](https://docs.mongodb.com/manual/installation/) or a mongo client like [Robo Mongo](https://robomongo.org/).

```
> use data_science_challenge
> show collections
> db.examples.find()
```

Each document consists of a dictionary with key-value pairs. Keys
 include `PatientBirthDate`, `PatientSex`, `PatientID`, and
  `PatientName`. Since 

## TODO: extract total dose of radiation

Radiation therapy is delivered in fractions. Each fraction usually corresponds to
a day where the patient visits a hospital to get treatment. The patient lies or
sits on a couch and a linear accelerator generates X-rays that are directed via 
one or more beams at the patient's tumor(s). A radiation
oncologist prescribes the total amount of radiation to be delivered measured in
[Grays (Gy)](https://en.wikipedia.org/wiki/Gray_(unit)) .


Write a new method `radiation_total_dose` for the `DicomParser`
class that takes a patient ID and returns the 
total dose of radiation in a treatment plan for that patient.

Then, based on the code in `extract_data_examples.py` create a new script called
`extract_data.py` and extract the total dose for each patient and 
create a document with `PatientID` and `radiation_total_dose` keys. Store the documents in a collection called `dicom`.

Some **hints** for doing this:

* Explore an [RT PLAN](http://localhost:8042/app/explorer.html) file.

* Take a look at the structure of [Fraction Group Sequence](https://dicom.innolitics.com/ciods/rt-plan/rt-fraction-scheme/300a0070) and [Referenced Beam Sequence](https://dicom.innolitics.com/ciods/rt-plan/rt-fraction-scheme/300a0070/300c0004)
in the DICOM standard.  Think about why there might be multiple fraction group sequences.

* Also take a look at [Dicompyler](https://github.com/bastula/dicompyler/blob/master/dicompyler/dicomparser.py) for some useful code.



# Loading data from clinical files

The clinical files include information about the radiation therapy delivered for each patient. Load that into mongo using
the following command.

```
mongoimport -d data_science_challenge -c radiation --type tsv --headerline --file data_warehouse/clinical/radiation.txt
```


## TODO: comparing extracted and clinical data

Compare the total dose extracted from the DICOM files with the clinical information. The following queries return all documents (the first `{}` is a query that matches all documents) projected down onto `PatientID` and `radiation_total_dose` (the projection contained in the second `{}`).

```
db.dicom.find({}, {'PatientID': 1, 'radiation_total_dose': 1})
db.radiation.find({}, {'bcr_patient_barcode': 1, 'radiation_total_dose': 1, 'radiation_adjuvant_units': 1})
```

Taking the clinical values as the ground truth. Are the results 
of the DICOM  data extraction accurate? If not, can you think of
reasons why they might differ? Can and should the
`radiation_total_dose` extraction method be altered to address 
any discrepancies?


# Predicting patient outcomes

Overall survival for cancer patients is often measured in terms
 of time from treatment to death or last contact, or survival
 rates at particular intervals (e.g. five-year survival rate).

Load `follow_up.txt` into another mongo collection. `last_contact_days_to` contains the number of days to last contact for a patient and `vital_status` records whether that
patient was alive or dead at the date of last contact.

## TODO: analyzing patient outcomes

Analyze the factors associated with patient survival. Note that this analysis is not restricted to patients with corresponding DICOM files. You can include additional fields of interest from other clinical files (e.g. `drug.txt`, [genomic data](https://gdc-portal.nci.nih.gov/projects/TCGA-HNSC), [tissue samples](https://portal.gdc.cancer.gov/legacy-archive/search/f?filters=%7B%22op%22:%22and%22,%22content%22:%5B%7B%22op%22:%22in%22,%22content%22:%7B%22field%22:%22files.data_format%22,%22value%22:%5B%22SVS%22%5D%7D%7D,%7B%22op%22:%22in%22,%22content%22:%7B%22field%22:%22cases.project.program.name%22,%22value%22:%5B%22TCGA%22%5D%7D%7D,%7B%22op%22:%22in%22,%22content%22:%7B%22field%22:%22cases.project.project_id%22,%22value%22:%5B%22TCGA-HNSC%22%5D%7D%7D%5D%7D)). 

Create a script in `data_science/` that can be run by the following command.

```
docker-compose run --rm data_science python NAME_OF_SCRIPT
```

Make sure to persist your model(s) to disk so that they can be
re-used later. 
Summarize the results of your analysis including one or 
two visualizations in a short two page document (e.g. markdown, pdf).

Some **suggestions** for doing this:

* [sklearn](scikit-learn.org/0.17/) has a wide range machine learning models for supervised learning (e.g. classification and regression)
* [lifelines](https://github.com/CamDavidsonPilon/lifelines) includes several survival analysis models in python with a similar API to sklearn
* `R` can be installed in the data science container as describe below and the `mongolite` package can be used to connect to mongo


# Modifying containers

If you want to install additional python packages, add them to the
`requirements.txt` file in the container directory.  These will be installed
via `pip`. For the changes to take effect, you'll need to rebuild the container.
For example, if you add a new package to the data warehouse requirements, run
the following command.

```
docker-compose build data_warehouse
```

If you want to install other additional packages in a container, modify the
`Dockerfile` in that container directory. For example, to install `R` on the
data_science container, you could add the following to the `Dockerfile` after 
the installation of python packages.

```
RUN apt-get update && apt-get install -y r-base r-base-dev
```
For changes to take effect you'll have to rebuild the container.

If you want to use different containers for the database or other components you can do so by modifying
`docker-compose.yml`. For example, you could use  [mysql](https://hub.docker.com/_/mysql/) or 
[postgres](https://hub.docker.com/_/postgres/) instead of mongo. This would
involve renaming the container, specifying the correct image, configuring
the appropriate ports, and making sure that the data warehouse is linked to
this new database container. You would also need to use different python packages to interact with the database.
