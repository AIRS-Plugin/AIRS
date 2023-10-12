# -*- coding: utf-8 -*-
"""
/***************************************************************************
 AIRS
                                 A QGIS plugin
 This plugin allows time series forecasting using deep learning models.
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2023-10-04
        copyright            : (C) 2023 by H. Naciri; N. Ben Achhab; F.E. Ezzaher; N. Raissouni
        email                : airs.qgis@gmail.com
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load AIRS class from file AIRS.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .artificial_intelligence_forecasting_remote_sensing import AIRS
    return AIRS(iface)
