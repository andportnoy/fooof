"""FOOOF - Group fitting object and methods."""

import os
from json import JSONDecodeError

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import gridspec

from fooof import FOOOF

###################################################################################################
###################################################################################################

class FOOOFGroup(FOOOF):

    def __init__(self, *args, **kwargs):

        FOOOF.__init__(self, *args, **kwargs)

        self._reset_group_results()


    def _reset_group_results(self):
        """Set (or reset) results to be empty."""

        self.group_results = []


    def model(self, freqs, psds, freq_range=None, save_dat=False, file_name='fooof_group_results', file_path=''):
        """Run FOOOF across a group of PSDs, then plot and print results.

        Parameters
        ----------
        freqs : 1d array
            Frequency values for the PSDs, in linear space.
        psds : 2d array
            Matrix of PSD values, in linear space. Shape should be [n_psds, n_freqs].
        freq_range : list of [float, float], optional
            Desired frequency range to run FOOOF on. If not provided, fits the entire given range.
        save_dat : bool, optional
            Whether to save data out to file while running. Default: False.
        file_name : str, optional
            File name to save to.
        file_path : str, optional
            Path to directory in which to save. If not provided, saves to current directory.
        """

        self.fit_group(freqs, psds, freq_range, save_dat, file_name, file_path)
        self.plot()
        self.print_results()


    def fit_group(self, freqs, psds, freq_range=None, save_dat=False, file_name='fooof_group_results', file_path=''):
        """Run FOOOF across a group of PSDs.

        Parameters
        ----------
        freqs : 1d array
            Frequency values for the PSDs, in linear space.
        psds : 2d array
            Matrix of PSD values, in linear space. Shape should be [n_psds, n_freqs].
        freq_range : list of [float, float], optional
            Desired frequency range to run FOOOF on. If not provided, fits the entire given range.
        save_dat : bool, optional
            Whether to save data out to file while running. Default: False.
        file_name : str, optional
            File name to save to.
        file_path : str, optional
            Path to directory in which to save. If not provided, saves to current directory.
        """

        # Clear results so that any prior data doesn't end up lumped together
        self._reset_group_results()

        # If saving, open a file to save to
        if save_dat:
            f_obj = open(os.path.join(file_path, file_name + '.json'), 'w')

        # Fit FOOOF across matrix of PSDs.
        #  Note: shape checking gets performed in fit - wrong shapes/orientations will fail there.
        for psd in psds:
            self.fit(freqs, psd, freq_range)
            self.group_results.append(self.get_results())
            if save_dat:
                self.save(f_obj, save_results=True)

        # Clear out last run PSD, but while keeping frequency information
        #  This is so that it doesn't retain data from an arbitrary PSD
        self._reset_dat(False)

        # If saving, close file
        if save_dat:
            f_obj.close()


    def get_group_results(self):
        """Return the results run across a group of PSDs."""

        return self.group_results


    def get_all_data(self, name, ind=None):
        """Return all data for a specified attribute across the group.

        Parameters
        ----------
        name : str
            Name of the data field to extract across the group.
        ind : int, optional
            Column index to extract from selected data, if requested.

        Returns
        -------
        out : ndarray
            Requested data.
        """

        # Pull out the requested data field from the group data
        out = np.array([getattr(dat, name) for dat in self.group_results])

        # Some data can end up as a list of separate arrays. If so, concatenate it all into one 2d array
        if isinstance(out[0], np.ndarray):
            out = np.concatenate([arr.reshape(1, len(arr)) if arr.ndim == 1 else arr for arr in out], 0)

        # Select out a specific column, if requested
        if ind is not None:
            out = out[:, ind]

        return out


    def plot(self, save_fig=False, save_name='FOOOF_fit.png', save_path=''):
        """Plot some data descriptions of the group data.

        Parameters
        ----------
        save_fig : boolean, optional
            Whether to save out a copy of the plot. default : False
        save_name : str, optional
            Name to give the saved out file.
        save_path : str, optional
            Path to directory in which to save. If not provided, saves to current directory.
        """

        fig = plt.figure(figsize=(14, 10))
        gs = gridspec.GridSpec(2, 2, height_ratios=[1, 1.2])

        ax0 = plt.subplot(gs[0, 0])
        self._plot_bg(ax0)

        ax1 = plt.subplot(gs[0, 1])
        self._plot_fit(ax1)

        ax2 = plt.subplot(gs[1, :])
        self._plot_oscs(ax2)

        if save_fig:
            plt.savefig(os.path.join(save_path, save_name))


    def create_report(self, save_name='FOOOFGroup_Report', save_path=''):
        """Generate and save out a report for the FOOOF Group results.

        Parameters
        ----------
        save_name : str, optional
            Name to give the saved out file.
        save_path : str, optional
            Path to directory in which to save. If not provided, saves to current directory.
        """

        # Set the font description for saving out text with matplotlib
        font = {'family': 'monospace',
                'weight': 'normal',
                'size': 16}

        # Initialize figure
        fig = plt.figure(figsize=(16, 20))
        gs = gridspec.GridSpec(3, 2, height_ratios=[1.5, 1.0, 1.2])

        # First / top: text results
        ax0 = plt.subplot(gs[0, :])
        results_str = self._gen_results_str()
        ax0.text(0.5, 0.0, results_str, font, ha='center')
        ax0.set_frame_on(False)
        ax0.set_xticks([])
        ax0.set_yticks([])

        # Add plots (same as from plot())
        ax1 = plt.subplot(gs[1, 0])
        self._plot_bg(ax1)

        ax2 = plt.subplot(gs[1, 1])
        self._plot_fit(ax2)

        ax3 = plt.subplot(gs[2, :])
        self._plot_oscs(ax3)

        # Save out the report
        plt.savefig(os.path.join(save_path, save_name + '.pdf'))
        plt.close()


    def load_group_results(self, file_name='fooof_group_results', file_path=''):
        """Load data from file, reconstructing the group_results.

        Parameters
        ----------
        file_name : str
            File from which to load data.
        file_path : str, optional
            Path to directory from which to load from. If not provided, saves to current directory.
        """

        # Clear results so as not to have possible prior results interfere
        self._reset_group_results()

        # Load from jsonlines file
        with open(os.path.join(file_path, file_name + '.json'), 'r') as f_obj:

            while True:

                # For each line, grab the FOOOFResults
                try:
                    self.load(f_obj)
                    self.group_results.append(self.get_results())

                # Break off when get a JSON error - end of the file
                except JSONDecodeError:
                    break

        # Reset peripheral data from last loaded result, keeping freqs info
        self._reset_dat(False)


    def _gen_results_str(self):
        """Generate a string representation of group fit results.

        Notes
        -----
        This overloads the equivalent method in FOOOF base object, for group results.
        - It therefore changes the behaviour (what is printed) for 'print_results'.
        """

        if not self.group_results:
            raise ValueError('Model fit has not been run - can not proceed.')

        # Set centering value
        cen_val = 100

        #
        sls = self.get_all_data('background_params', 1)
        cens = self.get_all_data('oscillations_params', 0)
        r2s = self.get_all_data('r2')
        errors = self.get_all_data('error')

        # Create output string
        output = '\n'.join([

            # Header
            '=' * cen_val,
            '',
            ' FOOOF - GROUP RESULTS'.center(cen_val),
            '',

            # Group information
            'Number of PSDs in the Group: {}'.format(len(self.group_results)).center(cen_val),
            '',

            # Frequency range and resolution
            'The input PSDs were modelled in the frequency range: {} - {} Hz'.format(
                int(np.floor(self.freq_range[0])), int(np.ceil(self.freq_range[1]))).center(cen_val),
            'Frequency Resolution is {:1.2f} Hz'.format(self.freq_res).center(cen_val),
            '',

            # Background parameters - knee fit status, and quick slope description
            'PSDs were fit {} knee fitting.'.format('with' if self.bg_use_knee else 'without').center(cen_val),
            '',
            'Background Slope Values'.center(cen_val),
            'Min: {:6.4f}, Max: {:6.4f}, Mean: {:5.4f}'.format(sls.min(), sls.max(), sls.mean()).center(cen_val),
            '',

            # Oscillation Parameters
            'In total {} oscillations were extracted from the group'.format(len(cens)).center(cen_val),
            '',

            # Fitting stats - error and r^2
            'Fitting Performance'.center(cen_val),
            '   R2s -  Min: {:6.4f}, Max: {:6.4f}, Mean: {:5.4f}'.format(r2s.min(), r2s.max(), r2s.mean()).center(cen_val),
            'Errors -  Min: {:6.4f}, Max: {:6.4f}, Mean: {:5.4f}'.format(errors.min(), errors.max(), errors.mean()).center(cen_val),
            '',

            # Footer
            '=' * cen_val
        ])

        return output


    def _plot_bg(self, ax=None):
        """Plot the background parameters, from across the group.

        Parameters
        ----------
        ax : matplotlib.Axes, optional
            Figure axes upon which to plot.
        """

        sls = self.get_all_data('background_params', 1)

        if not ax:
            fig, ax = plt.subplots()

        ax.scatter(np.zeros_like(sls) + np.random.normal(0, 0.025, sls.shape), sls, s=36, alpha=0.5)

        ax.set_title('Slope Values', fontsize=16)
        ax.set_ylabel('Slope Value', fontsize=12)

        plt.xticks([0], ['Slope'], fontsize=12)

        ax.set_xlim([-0.4, 0.4])


    def _plot_fit(self, ax=None):
        """Plot the goodness of fit measures - error & r^2, across the group.

        Parameters
        ----------
        ax : matplotlib.Axes, optional
            Figure axes upon which to plot.
        """

        errs = self.get_all_data('error')
        r2s = self.get_all_data('r2')

        if not ax:
            fig, ax = plt.subplots()

        ax1 = ax.twinx()

        ax.scatter(np.zeros_like(errs) + np.random.normal(0, 0.025, errs.shape), errs, s=36, alpha=0.5)
        ax.set_ylabel('Error', fontsize=12)

        ax1.scatter(np.ones_like(r2s) + np.random.normal(0, 0.025, r2s.shape), r2s, s=36, alpha=0.5)
        ax1.set_ylabel('R^2', fontsize=12)

        ax.set_xlim([-0.5, 1.5])

        ax.set_title('Goodness of Fit', fontsize=16)

        plt.xticks([0, 1], ['Error', 'R^2'], fontsize=12)


    def _plot_oscs(self, ax=None):
        """Plot the oscillations parameters, from across the group.

        Parameters
        ----------
        ax : matplotlib.Axes, optional
            Figure axes upon which to plot.
        """

        cens = self.get_all_data('oscillations_params', 0)

        if not ax:
            fig, ax = plt.subplots()

        ax.hist(cens, 20, alpha=0.8);

        ax.set_title('Oscillations - Center Frequencies', fontsize=16)
        ax.set_xlabel('Frequency', fontsize=12)
        ax.set_ylabel('Count', fontsize=12)


FOOOFGroup.__doc__ = FOOOF.__doc__