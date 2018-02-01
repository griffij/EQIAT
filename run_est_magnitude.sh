#PBS -P n74
#PBS -q express
#PBS -l walltime=8:00:00
#PBS -l ncpus=1
#PBS -l mem=16GB
#PBS -l wd

module load intel-cc/12.1.9.293
module load intel-fc/12.1.9.293
module load gdal
module load geos/3.5.0
module load hdf5/1.8.10
#module load openmpi/1.6.3
module unload python
module load python/2.7.11
module load python/2.7.11-matplotlib

# To get rtree to run
export SPATIALINDEX_C_LIBRARY=/short/n74/jdg547/spatialindex-src-1.8.5/lib/libspatialindex_c.so.4
export LD_LIBRARY_PATH=/short/n74/jdg547/spatialindex-src-1.8.5/lib:$LD_LIBRARY_PATH
# Python paths for local openquake installs and dependencies
export PYTHONPATH=.:/home/547/jdg547/.local/lib/python2.7/site-packages:${PYTHONPATH}
export PYTHONPATH=.:/short/w84/NSHA18/sandpit/jdg547/oq-hazardlib:${PYTHONPATH}
export PYTHONPATH=.:/short/w84/NSHA18/sandpit/jdg547/oq-engine:${PYTHONPATH}

#python estimate_magnitude.py -param_file data/1699_params.txt >& parjob_1699_weighted_mod.log
#python estimate_magnitude.py -param_file data/1699megathrust_params.txt >& parjob_1699_weighted_megathrust.log
python estimate_magnitude.py -param_file data/1867_params.txt >& parjob_1867_weighted.log
#python estimate_magnitude.py -param_file data/1847_params.txt >& parjob_1847_weighted.log
#python estimate_magnitude.py -param_file data/1780_params.txt >& parjob_1780_weighted.log
#python estimate_magnitude.py -param_file data/1699megathrust_params.txt >& data/1699megathrust_params.txt.log
#python estimate_magnitude.py -param_file data/1820_M8.4_params.txt >& data/1820_M8.4_params.txt.log