from PyQt5.QtWidgets import QStyledItemDelegate, QStyle, QApplication, QStyleOptionViewItem
from PyQt5.QtGui import QTextDocument
from PyQt5.QtCore import Qt, QSize, QRectF


class RichTextDelegate(QStyledItemDelegate):
    """
    A delegate to render rich HTML text in a QListWidget item
    while preserving selection highlighting and calculating proper size.
    """
    def paint(self, painter, option, index):
        options = QStyleOptionViewItem(option)
        self.initStyleOption(options, index)

        # Prevent the base class from drawing the text
        options.text = ""
        style = option.widget.style() if option.widget else QApplication.style()
        style.drawControl(QStyle.CE_ItemViewItem, options, painter)

        # Prepare a QTextDocument to render the HTML
        doc = QTextDocument()
        doc.setHtml(index.data(Qt.DisplayRole))
        doc.setTextWidth(options.rect.width())

        painter.save()
        # Rysuj HTML
        text_rect = style.subElementRect(QStyle.SE_ItemViewItemText, options)
        painter.translate(text_rect.topLeft())
        clip = QRectF(0, 0, text_rect.width(), text_rect.height())
        doc.drawContents(painter, clip)
        painter.restore()

    def sizeHint(self, option, index):
        options = QStyleOptionViewItem(option)
        self.initStyleOption(options, index)
        doc = QTextDocument()
        doc.setHtml(options.text)
        doc.setTextWidth(options.rect.width())
        return QSize(int(doc.idealWidth()), int(doc.size().height()) + 5)