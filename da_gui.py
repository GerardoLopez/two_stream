import numpy as np
import matplotlib.pyplot as plt

from IPython.display import display

# Lots of different places that widgets could come from...

try:
    from ipywidgets import interact, FloatSlider, IntSlider, Dropdown, Checkbox, IntProgress
except ImportError:
    try:
        from IPython.html.widgets import interact, FloatSlider, IntSlider, Dropdown, Checkbox, IntProgress
    except ImportError:
        try:
            from IPython.html.widgets import (interact, CheckboxWidget as Checkbox,
                                              FloatSliderWidget as FloatSlider,
                                              IntSliderWidget as IntSlider)
        except ImportError:
            pass


from tip_helpers import retrieve_albedo
from eoldas_machinery import tip_inversion, regularised_tip_inversion

logo = plt.imread ( "nceologo200.gif")

sites ="""AU-Tum
BR-Cax
CA-Ca1
DE-Geb
DE-Hai
ES-LMa
FI-Hyy
FR-Lam
IT-SRo
RU-Ylr
US-Brw
US-Bar
US-Bo1
US-Dk2
US-Ha2
US-Ne1
US-Ne2
US-Ne3
US-Me2
US-Me3
US-MMS
US-Ton
SE-Abi
ZA-Kru""".split("\n")

tip_params = [ r'$\omega_{vis}\; [-]$', r'$d_{vis}\; [-]$', r'$\alpha_{vis}\; [-]$',
              r'$\omega_{nir}\; [-]$', r'$d_{nir}\; [-]$', r'$\alpha_{nir}\; [-]$',
              r'$LAI_{eff}\;[m^{2}m^{-2}]$' ]

def visualise_albedos():
    @interact ( fluxnet_site=Dropdown(options=sites), year=IntSlider(min=2004,max=2013, step=1))
    def plot_albedos ( fluxnet_site, year ):
        observations, mask, bu, passer_snow = retrieve_albedo(year, fluxnet_site,
                                                              [0.05, 0.07])
        passer = mask[:,1] == 1
        doys = mask[:, 0]
        plt.figure ( figsize=(12,6))
        plt.plot ( doys[passer], observations[passer, 0], 'o', label="Visible Albedo")
        plt.plot ( doys[passer], observations[passer, 1], 'o', label="Near-infrarred Albedo")
        plt.vlines ( doys[passer], observations[passer, 0] + 1.96*bu[passer,0],
                     observations[passer, 0] - 1.96 * bu[passer, 0])
        plt.vlines ( doys[passer], observations[passer, 1] + 1.96*bu[passer,1],
                     observations[passer, 1] - 1.96 * bu[passer, 1])
        plt.legend(loc="best", numpoints=1, fancybox=True, shadow=True)
        plt.ylabel("Bi-hemispherical reflectance [-]")
        plt.xlabel("DoY/%d" % year )
        plt.xlim ( 1, 368)
        plt.ylim ( 0, 0.7)
        ax1 = plt.gca()
        ax1.figure.figimage(logo, 60, 60, alpha=.1, zorder=1)

        # Hide the right and top spines
        ax1.spines['right'].set_visible(False)
        ax1.spines['top'].set_visible(False)
        # Only show ticks on the left and bottom spines
        ax1.yaxis.set_ticks_position('left')
        ax1.xaxis.set_ticks_position('bottom')


def single_observation_inversion():
    display(f)
    @interact ( fluxnet_site=Dropdown(options=sites),
                year=IntSlider(min=2004,max=2013, step=1),
                green_leaves=Checkbox(description="Assume green leaves", default=False),
                __manual=True )
    def tip_single_observation ( fluxnet_site, year, green_leaves,
                                       n_tries=5 ):

        f = IntProgress( min=0, max=n_tries+1 )
        f.value = 1


        retval_s, state, obs = tip_inversion( year, fluxnet_site,
                                              green_leaves=green_leaves,
                                              n_tries=n_tries, progressbar=f)
        mu = state.operators['Prior'].mu
        cinv = state.operators['Prior'].inv_cov
        c = np.array(np.sqrt(np.linalg.inv (cinv.todense()).diagonal())).squeeze()


        fig, axs = plt.subplots(nrows=5, ncols=2, figsize=(14, 12))
        axs = axs.flatten()
        fig.suptitle("%s (%d)" % (fluxnet_site, year), fontsize=18)
        params = ['omega_vis', 'd_vis', 'a_vis', 'omega_nir', 'd_nir', 'a_nir', 'lai']
        post_sd = np.sqrt(np.array(retval_s['post_cov'].todense()).squeeze())
        post_sd = np.where(post_sd > c, c, post_sd)

        for i, p in enumerate(tip_params):

            # plt.fill_between ( state.state_grid, retval['real_ci5pc'][p],
            #                   retval['real_ci95pc'][p], color="0.8" )
            # plt.fill_between ( state.state_grid, retval['real_ci25pc'][p],
            #                   retval['real_ci75pc'][p], color="0.6" )

            axs[i].axhspan(mu[(i*46):((i+1)*46)][0]+c[(i*46):((i+1)*46)][0],
                           mu[(i*46):((i+1)*46)][0] - c[(i * 46):((i + 1) * 46)][0], color="0.9" )

            axs[i].plot(state.state_grid, mu[(i * 46):((i + 1) * 46)], '--')
            axs[i].plot(state.state_grid, retval_s['real_map'][params[i]], 'o-', mfc="none")

            axs[i].vlines ( state.state_grid, retval_s['real_map'][params[i]] - post_sd[(i*46):((i+1)*46)],
                            retval_s['real_map'][params[i]] + post_sd[(i*46):((i+1)*46)], lw=0.8, colors="0.1", alpha=0.5)



            if i in [ 1, 4, 6]:
                axs[i].set_ylim(0, 6)
            else:
                axs[i].set_ylim(0, 1)
            axs[i].set_ylabel( tip_params[i] )

        fwd = np.array(obs.fwd_modelled_obs)
        axs[7].plot(obs.observations[:, 0], fwd[:, 0], 'k+', label="VIS")
        axs[7].plot(obs.observations[:, 1], fwd[:, 1], 'rx', label="NIR")
        axs[7].set_xlabel("Measured BHR [-]")
        axs[7].set_ylabel("Predicted BHR [-]")
        axs[7].plot ( [0,0.9], [0, 0.9], 'k--', lw=0.5)
        axs[7].legend(loc='best')


        axs[8].vlines(obs.mask[:, 0], obs.observations[:, 0] - 1.96 * obs.bu[:, 0],
                      obs.observations[:, 0] + 1.96 * obs.bu[:, 0])
        axs[8].plot(obs.mask[:, 0], obs.observations[:, 0], 'o')

        axs[9].vlines(obs.mask[:, 0], obs.observations[:, 1] - 1.96 * obs.bu[:, 1],
                      obs.observations[:, 1] + 1.96 * obs.bu[:, 1])
        axs[9].plot(obs.mask[:, 0], obs.observations[:, 1], 'o')

        axs[8].set_ylabel("BHR VIS [-]")
        axs[9].set_ylabel("BHR NIR [-]")
        axs[8].set_xlabel("DoY [d]")
        axs[9].set_xlabel("DoY [d]")

        for i in xrange(10):

            if i != 7:
                axs[i].set_xlim(1, 370)
            # Hide the right and top spines
            axs[i].spines['right'].set_visible(False)
            axs[i].spines['top'].set_visible(False)
            # Only show ticks on the left and bottom spines
            axs[i].yaxis.set_ticks_position('left')
            axs[i].xaxis.set_ticks_position('bottom')

        fig.figimage(logo, fig.bbox.xmax - 500, fig.bbox.ymax - 250, alpha=.4, zorder=1)#if __name__ == "__main__":
    #print plot_albedos ( "DE-Geb", 2004)
    #solve_tip_single_observation( "DE-Geb", 2008, False)