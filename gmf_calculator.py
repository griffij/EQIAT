"""Generate ground motion fields using OpenQuake functions for locations 
where we have MMI observations. This builds a dataset by which to find 
the best fit event

Jonathan Griffin
Geoscience Australia, December 2016
"""

import os, sys
import numpy as np
from scipy.stats import norm
from scipy import interpolate
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from openquake.hazardlib.calc.gmf import GmfComputer
from openquake.hazardlib.nrml import SourceModelParser
from openquake.hazardlib.sourceconverter import SourceConverter, \
    area_to_point_sources, SourceGroup
from RSA2MMI import rsa2mmi8


def get_pt_sources(area_source_file, discretisation=50.):
    """Calls OpenQuake parsers to read area source model
    from source_mode.xml type file, convert to point sources
    and return to calculate ruptures.
    :params area_source_file:
        nrml format file of the area source
    :params discretisation:
        Grid size (km) for the area source discretisation, 
        which defines the distance between resulting point
        sources.
    :returns new_pt_sources
        Point source for the area source model
    """
    converter = SourceConverter(50, 10, width_of_mfd_bin=0.1,
                                area_source_discretization=discretisation)
    parser = SourceModelParser(converter)
    try:
        sources = parser.parse_sources(area_source_file)
    except AttributeError: # Handle version 2.1 and above
        sources = []
        groups = parser.parse_src_groups(area_source_file)
        for group in groups:
            for source in group:
                sources.append(source)
    name = 'test_point_model'
    new_pt_sources = {}
    for source in sources:
        pt_sources = area_to_point_sources(source)
        for pt in pt_sources:
            pt.source_id = pt.source_id.replace(':','')
            pt.name = pt.name.replace(':','_')
            try:
                new_pt_sources[pt.tectonic_region_type].append(pt)
            except KeyError:
                new_pt_sources[pt.tectonic_region_type] = [pt]
    return new_pt_sources

def get_sources(source_model_file, discretisation=50.):
    """Calls OpenQuake parsers to read  source model
    from source_mode.xml type file, 
    and return to calculate ruptures. A more generic verions
    than that above.
    :params source_model_file:
        nrml format file of source model
    :params discretisation:
        Grid size (km) for the area source discretisation, 
        which defines the distance between resulting point
        sources.
    :returns sources
        Source for the source model
    """
    converter = SourceConverter(50, 10, width_of_mfd_bin=0.1,
                                area_source_discretization=discretisation)
    parser = SourceModelParser(converter)
    try:
        sources = parser.parse_sources(source_model_file)
    except AttributeError: # Handle version 2.1 and above
        sources = []
        groups = parser.parse_src_groups(source_model_file)
        for group in groups:
            for source in group:
                sources.append(source)
#    name = 'test_point_model'
    new_sources = {}
    for source in sources:
        #pt_sources = area_to_point_sources(source)
        #for pt in pt_sources:
        #    pt.source_id = pt.source_id.replace(':','')
        #    pt.name = pt.name.replace(':','_')
            try:
                new_sources[source.tectonic_region_type].append(source)
            except KeyError:
                new_sources[source.tectonic_region_type] = [source]
    return new_sources

class RuptureGmf(object):
    """Class for storing ruptures and associated
    ground motion fields for later analysis
    """

    def __init__(self, sources, gsim, sitecol, imts = ['SA(1.0)']):
        """
        :params sources:
            Source objects derived from original area source model
        :params gsim:
            GSIM instance (i.e. subclass of openquake.hazardlib.gsim.base.GMPE)
        """
        self.sources = sources
        self.gsim  = gsim
        self.imts = imts
        self.sitecol = sitecol
        self.rupture_list = [] # list for storing ruptures
        self.gmf_list = [] # list for storing associated gmfs
        self.mmi_list = []
    
    def calculate_from_pts(self):
        """Generates ruptures for each pt source and calculates ground motion
        field.
        :returns gmfs:
            Set of ruptures and associated parameters for ground motion
            calculations  
        """
        for pt in self.sources:
            #        rupture_mags = []
            #        rupture_hypocenter = []
            ruptures = pt.iter_ruptures()
            for rupture in ruptures:
                computer = GmfComputer(rupture, self.sitecol,
                                       self.imts, [self.gsim],
                                       truncation_level=0)
                gmf = computer.compute(self.gsim, 1)
                gmf = gmf.flatten()
                self.rupture_list.append(rupture)
                self.gmf_list.append(gmf)

    def calculate(self):
        """Generates ruptures for each source and calculates ground motion
        field.
        :returns gmfs:
            Set of ruptures and associated parameters for ground motion
            calculations  
        """
        for source in self.sources:
            #        rupture_mags = []
            #        rupture_hypocenter = []
            ruptures = source.iter_ruptures()
            for rupture in ruptures:
                #print type(rupture)
                #print 'Calculating rupture', rupture.hypocenter
                computer = GmfComputer(rupture, self.sitecol,
                                       self.imts, [self.gsim],
                                       truncation_level=0)
                gmf = computer.compute(self.gsim, 1)
                gmf = gmf.flatten()
                self.rupture_list.append(rupture)
                self.gmf_list.append(gmf)

    def calculate_from_rupture(self, rupture, rup_sitecol=None):
        """Method to generate scenario ground motion
        for a specific rupture
        """
        if rup_sitecol is None:
            rup_sitecol = self.sitecol
        computer = GmfComputer(rupture, rup_sitecol,
                               self.imts, [self.gsim],
                               truncation_level=0)
        gmf = computer.compute(self.gsim, 1)
        gmf = gmf.flatten()
        print 'gmf', gmf
        self.rupture_scenario = rupture
        self.rupture_gmf = gmf
        self.rupture_gmf_mmi = rsa2mmi8(gmf, period = 1.0)
        

    def rsa2mmi(self):
        """Convert ground motion fields to MMI intensity
        """
        for gmf in self.gmf_list:
            mmi = rsa2mmi8(gmf, period = 1.0)
            self.mmi_list.append(mmi)

    def calc_sum_squares_mmi(self, mmi_obs):
        """Calculates sum of squares for each rupture gmf compared 
        with historical observations
        """
        self.sum_squares_list = []
        for mmi in self.mmi_list:
            sum_squares = np.sum((mmi - mmi_obs)**2)
            self.sum_squares_list.append(sum_squares)

    def calc_rmse(self, mmi_obs, weights = None):
        """Calculates root-mean-square error of each rupture gmf
        compared with historical observations
        """
        self.mmi_obs = mmi_obs
        try:
            self.sum_squares_list
        except AttributeError:
            if weights is not None:
                self.calc_sum_squares_mmi_weighted(self.mmi_obs, weights)
                self.rmse = np.sqrt(np.array(self.sum_squares_list))
            else:
                self.calc_sum_squares_mmi(self.mmi_obs)
                self.rmse = np.sqrt(np.array(self.sum_squares_list)/float(len(self.mmi_obs)))

    def calc_sum_squares_mmi_weighted(self, mmi_obs, weights):
        """Calculates sum of squares for each rupture gmf compared 
        with historical observations
        """
        self.sum_squares_list = []
#        weights = np.where(mmi_obs < 5, 2, 1) # Increase weight for low MMI events
        for mmi in self.mmi_list:
            #sum_squares = np.sum(np.dot(weights,(mmi - mmi_obs))**2)/(np.sum(weights**2))
#            print weights
            weights = np.array(weights)
            weights = weights*(1./sum(weights)) # Normalise weights to sum to 1
#            print weights
#            print sum(weights)
            sum_squares = np.dot(weights,(mmi - mmi_obs)**2)
#            sum_squares = np.sum(np.dot(weights,(mmi - mmi_obs))**2)
            self.sum_squares_list.append(sum_squares)

    def find_best_fit(self):
        """Find rupture with minimm sum of squares
        """
        index = np.argmin(self.rmse)
        self.best_rupture = self.rupture_list[index]
        self.min_rmse = self.rmse[index]

    def uncertainty_model(self):
        """Estimate parameter uncertainties by 
        assuming the rmse is maximum likelihood.
        We use the residuals of the best-fit parameters 
        to estimate the standard deviation of the model fit
        """
        if len(self.mmi_obs) <= 6:
            print 'Not enough data points to calculate uncertainties'
            indices = np.where(self.rmse < 1e24)[0]
        else:
            self.sigma=(1./(len(self.mmi_obs)-6))*np.power(min(self.rmse),2)
            print self.sigma
            self.uncert_fun = norm(min(self.rmse),self.sigma)
            print self.uncert_fun.ppf(0.975)
            indices = np.where(self.rmse < self.uncert_fun.ppf(0.975))[0]
        print 'max rmse', max(self.rmse)
        # all ruptures within 95% uncertainty bounds 
        self.fitted_ruptures = []
#        print indices
        for index in indices:
#            print index
            self.fitted_ruptures.append(self.rupture_list[index])
        # Create lists for storing ranges of each parameter
        self.fitted_mags = []
        self.fitted_lons = []
        self.fitted_lats = []
        self.fitted_depths = []
        self.fitted_strikes = []
        self.fitted_dips = []
        for rup in self.fitted_ruptures:
            self.fitted_mags.append(rup.mag)
            self.fitted_lons.append(rup.hypocenter.longitude)
            self.fitted_lats.append(rup.hypocenter.latitude)
            self.fitted_depths.append(rup.hypocenter.depth)
            self.fitted_strikes.append(rup.surface.get_strike())
            self.fitted_dips.append(rup.surface.get_dip())
        self.min_mag = min(self.fitted_mags)
        self.max_mag = max(self.fitted_mags)
        self.min_lon = min(self.fitted_lons)
        self.max_lon = max(self.fitted_lons)
        self.min_lat = min(self.fitted_lats)
        self.max_lat = max(self.fitted_lats)
        self.min_depth = min(self.fitted_depths)
        self.max_depth = max(self.fitted_depths)
        self.min_strike = min(self.fitted_strikes)
        self.max_strike = max(self.fitted_strikes)
        self.min_dip = min(self.fitted_dips)
        self.max_dip = max(self.fitted_dips)
        print 'strikes',  np.unique(np.array(self.fitted_strikes))
        print 'dips', np.unique(np.array(self.fitted_dips))

    def uncertainty_slice(self, x, y, z, zvalue, fig_comment=None):
        """ Get 2D slices of uncertainty model for plotting
        :params x:
            Quantity to be used for x-axis
        :params y:
            Quantity to be used for y-axis
        :params z:
            Quantity we are slicing across
        :params zvalue:
            Value of z at which the othe dimensions will be sliced
        :params fig_comment:
            String to be appended to figure name
        """
        # Generate uncertainty model if doesnt already exist
    #    if not hasattr(self, uncert_fun):
    #        self.uncertainty_model() 
    #    if z='mag':

        # Create an array of rupture parameters
        mags = np.array([rup.mag for rup in self.rupture_list])
        lons = np.array([rup.hypocenter.longitude for rup in self.rupture_list])   
        lats = np.array([rup.hypocenter.latitude for rup in self.rupture_list])
        depths = np.array([rup.hypocenter.depth for rup in self.rupture_list]) 
        strikes = np.array([rup.surface.get_strike() for rup in self.rupture_list]) 
        dips = np.array([rup.surface.get_dip() for rup in self.rupture_list]) 

#        print mags
        parameter_space = np.vstack([mags,lons,lats,depths,strikes,dips])
        parameter_dict = {'mag': 0, 'longitude': 1,
                          'latitude': 2, 'depth': 3,
                          'strike': 4, 'dip':5}
        indices = np.where(parameter_space[parameter_dict[z]] == zvalue)
        #indices = np.where(np.isclose(parameter_space[parameter_dict[z]], zvalue, rtol=1e-5) == True)
        xvalues = parameter_space[parameter_dict[x], indices][0]
        yvalues = parameter_space[parameter_dict[y], indices][0]
#        print xvalues, len(xvalues)
#        print yvalues, len(yvalues)
        rmse_subset = self.rmse[indices]
#        print 'rmse_subset'
#        print rmse_subset, len(rmse_subset)
#        print 'min(rmse_subset)', min(rmse_subset)
#        print np.argmin(self.rmse)
#        print np.argmin(rmse_subset)
        # now get lowest rmse for each combination of remaining parameters at each 
        # xy point
        rmse_list = []
        xs = []
        ys = []
        for xi in np.unique(xvalues):
            for yi in np.unique(yvalues):
                j = np.where(xvalues==xi)
                k = np.where(yvalues == yi)
                i = np.intersect1d(j,k) # Get all locations matching both x, y locations
 #               print j
 #               print k
 #               print 'i', i
 #               print xvalues[j]
 #               print yvalues[k]
 #               print self.rmse[i]
 #               print rmse_subset[i]
#                print 'self.rmse[i]', self.rmse[i]
                if len(i) > 0:
 #                   print 'self.rmse[i]', self.rmse[i]
 #                   print 'min(self.rmse[i])', min(self.rmse[i])
 #                   print 'min(rmse_subset[i])', min(rmse_subset[i])
                    rmse_list.append(min(rmse_subset[i]))
                    xs.append(xi)
                    ys.append(yi)
#        print rmse_list
        rmse_subset = np.array(rmse_list)
        xs = np.array(xs)
        ys = np.array(ys)
        print 'rmse_subset', rmse_subset
#        xvalues = np.unique(xvalues)
#        yvalues = np.unique(yvalues)
#        xy = np.mgrid(np.unique(xvalues), np.unique(yvalues))
#        print xy
#        print xy[0][0], len(xy[0][0])
#        for i in range(len(xy[0][0])):
            
#        print 'xs', xs
#        print 'ys', ys
#        print rmse_subset
#        print xvalues
#        print yvalues
        xx,yy = np.mgrid[min(xvalues):max(xvalues):0.02,min(yvalues):max(yvalues):0.01]
        #xx,yy=np.meshgrid(xs, ys)
        rmse_grid = interpolate.griddata((xs, ys), rmse_subset, (xx,yy), method='nearest')
#        print xx, len(xx)
#        print yy, len(yy)
#        print rmse_grid, len(rmse_grid)

        plt.clf()
        try:
            CS1=plt.contour(xx, yy, rmse_grid, levels = [self.sigma, self.uncert_fun.ppf(0.975)], linewidths=0.5, colors='k')
        except AttributeError:
            pass
        except ValueError:
            print 'only one best fit locations, cannnot plot locations uncertainty'
            pass
#        CS2=plt.contourf(xx, yy, rmse_grid, 8,vmax=np.max(rmse_grid), vmin=np.min(rmse_grid))
        try:
            CS2=plt.contourf(xx, yy, rmse_grid, 8,vmax=max(self.rmse), vmin=min(self.rmse))
#        CS2=plt.contourf(xs, ys, rmse_subset, 8,vmax=max(self.rmse), vmin=min(self.rmse)) 
            cbar = plt.colorbar(CS2)
            cbar.ax.set_ylabel('RMSE')
            figname = 'rmse_slice_%s_%s_%.2f_%s_%s_%s.png' % (
                fig_comment, z, zvalue, x, y, self.gsim)
            figname = figname.replace('()', '')
            plt.savefig(figname)
        except ValueError:
            print 'only one best fit locations, cannnot plot locations uncertainty'
            pass
        
                                        
        return xs, ys, rmse_subset

    

