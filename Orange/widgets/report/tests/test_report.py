import unittest
from importlib import import_module
import os
import warnings

import AnyQt

from Orange.data.table import Table
from Orange.classification import LogisticRegressionLearner
from Orange.classification.tree import TreeLearner
from Orange.evaluation import CrossValidation
from Orange.distance import Euclidean
from Orange.widgets.report.owreport import OWReport
from Orange.widgets.widget import OWWidget
from Orange.widgets.tests.base import WidgetTest
from Orange.widgets.visualize.owtreeviewer import OWTreeGraph
from Orange.widgets.evaluate.owcalibrationplot import OWCalibrationPlot
from Orange.widgets.evaluate.owliftcurve import OWLiftCurve
from Orange.widgets.evaluate.owrocanalysis import OWROCAnalysis
from Orange.widgets.evaluate.owtestandscore import OWTestAndScore
from Orange.widgets.unsupervised.owcorrespondence import OWCorrespondenceAnalysis
from Orange.widgets.unsupervised.owdistancemap import OWDistanceMap
from Orange.widgets.unsupervised.owdistances import OWDistances
from Orange.widgets.unsupervised.owhierarchicalclustering import OWHierarchicalClustering
from Orange.widgets.unsupervised.owkmeans import OWKMeans
from Orange.widgets.unsupervised.owmds import OWMDS
from Orange.widgets.unsupervised.owpca import OWPCA


def get_owwidgets(top_module_name):
    top_module = import_module(top_module_name)
    widgets = []
    for root, _, files in os.walk(top_module.__path__[0]):
        root = root[len(top_module.__path__[0]):].lstrip(os.path.sep)
        for file in files:
            if file.lower().startswith('ow') and file.lower().endswith('.py'):
                module_name = "{}.{}".format(
                    top_module_name,
                    os.path.join(root, file).replace(os.path.sep, '.')[:-len('.py')])
                try:
                    module = import_module(module_name,
                                           top_module_name[:top_module_name.index('.')])
                except (ImportError, RuntimeError):
                    warnings.warn('Failed to import module: ' + module_name)
                    continue
                for name, value in module.__dict__.items():
                    if (name.upper().startswith('OW') and
                            isinstance(value, type) and
                            issubclass(value, OWWidget) and
                            getattr(value, 'name', None) and
                            getattr(value, 'send_report', None)):
                        widgets.append(value)
    return list(set(widgets))


DATA_WIDGETS = get_owwidgets('Orange.widgets.data')
VISUALIZATION_WIDGETS = get_owwidgets('Orange.widgets.visualize')
MODEL_WIDGETS = get_owwidgets('Orange.widgets.model')


class TestReportWidgets(WidgetTest):
    model_widgets = MODEL_WIDGETS
    data_widgets = DATA_WIDGETS
    eval_widgets = [OWCalibrationPlot, OWLiftCurve, OWROCAnalysis]
    unsu_widgets = [OWCorrespondenceAnalysis, OWDistances, OWKMeans,
                    OWMDS, OWPCA]
    dist_widgets = [OWDistanceMap, OWHierarchicalClustering]
    visu_widgets = VISUALIZATION_WIDGETS
    spec_widgets = [OWTestAndScore, OWTreeGraph]

    def _create_report(self, widgets, rep, data):
        for widget in widgets:
            w = self.create_widget(widget)
            if w.inputs and isinstance(data, w.inputs[0].type):
                handler = getattr(w, w.inputs[0].handler)
                handler(data)
                w.create_report_html()
            rep.make_report(w)
            # rep.show()

    def test_report_widgets_model(self):
        rep = OWReport.get_instance()
        data = Table("titanic")
        widgets = self.model_widgets

        w = self.create_widget(OWTreeGraph)
        clf = TreeLearner(max_depth=3)(data)
        clf.instances = data
        w.ctree(clf)
        w.create_report_html()
        rep.make_report(w)

        self._create_report(widgets, rep, data)

    def test_report_widgets_data(self):
        rep = OWReport.get_instance()
        data = Table("zoo")
        widgets = self.data_widgets
        self._create_report(widgets, rep, data)

    def test_report_widgets_evaluate(self):
        rep = OWReport.get_instance()
        data = Table("zoo")
        widgets = self.eval_widgets
        cv = CrossValidation(k=3, store_data=True)
        results = cv(data, [LogisticRegressionLearner()])
        results.learner_names = ["LR l2"]

        w = self.create_widget(OWTestAndScore)
        w.insert_learner(0, LogisticRegressionLearner())
        w.set_train_data(data)
        w.set_test_data(data)
        w.create_report_html()
        rep.make_report(w)

        self._create_report(widgets, rep, results)

    def test_report_widgets_unsupervised(self):
        rep = OWReport.get_instance()
        data = Table("zoo")
        widgets = self.unsu_widgets
        self._create_report(widgets, rep, data)

    def test_report_widgets_unsupervised_dist(self):
        rep = OWReport.get_instance()
        data = Table("zoo")
        dist = Euclidean(data)
        widgets = self.dist_widgets
        self._create_report(widgets, rep, dist)

    def test_report_widgets_visualize(self):
        rep = OWReport.get_instance()
        data = Table("zoo")
        widgets = self.visu_widgets
        self._create_report(widgets, rep, data)

    @unittest.skipIf(AnyQt.USED_API == "pyqt5", "Segfaults on PyQt5")
    def test_report_widgets_all(self):
        rep = OWReport.get_instance()
        widgets = self.model_widgets + self.data_widgets + self.eval_widgets + \
                  self.unsu_widgets + self.dist_widgets + self.visu_widgets + \
                  self.spec_widgets
        self._create_report(widgets, rep, None)


if __name__ == "__main__":
    unittest.main()
