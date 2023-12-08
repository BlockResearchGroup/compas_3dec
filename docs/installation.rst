********************************************************************************
Installation
********************************************************************************

Stable
======

Stable releases of :mod:`compas_3dec` can be installed via ``conda-forge``.

.. code-block:: bash

    conda create -n c3dec -c conda-forge compas_3dec

Several examples use the COMPAS Viewer for visualisation.
To install :mod:`compas_view2` in the same environment

.. code-block:: bash

    conda activate c3dec
    conda install compas_view2

Or everything in one go

.. code-block:: bash

    conda create -n c3dec -c conda-forge compas_3dec compas_view2

Dev Install
===========

See :doc:`devguide`.
