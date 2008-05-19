#ifndef SMEWTD_H
#define SMEWTD_H

#include <QApplication>
#include <QStringList>
#include <QtDBus>
#include <QDBusAbstractAdaptor>
#include "storageproxy.h"
#include "settings.h"

namespace smewt {


class Smewtd : public QDBusAbstractAdaptor {

  Q_OBJECT

  Q_CLASSINFO("D-Bus Interface", "com.smewt.Smewt.Smewtd")
  Q_PROPERTY(QString organizationName READ organizationName)
  Q_PROPERTY(QString organizationDomain READ organizationDomain)


 protected:
  QApplication* _app;
  StorageProxy* _storage;


 public:

  Settings* settings;
  // Config property list
  /*
  QList<Friend> friends;
  QString incomingFolder;
  QString storageDomain;
  QString idKey;
  */


  Smewtd(QApplication *app) : QDBusAbstractAdaptor(app), _app(app) {
    connect(app, SIGNAL(aboutToQuit()), SIGNAL(aboutToQuit()));

    //readConfig();
    settings = new Settings(app);

    _storage = new StorageProxy(settings->storageDomain, this);
  }

  ~Smewtd() {
    //saveConfig();
    delete settings;
    delete _storage;
  }

  Friend getFriend(const QString& friendName) const;

  //void readConfig();
  //void saveConfig();

 public:

  QString organizationName() {
    return _app->organizationName();
  }

  QString organizationDomain() {
    return _app->organizationDomain();
  }

 public slots:
 //void reset();
  
  bool ping();

  void startDownload(QString friendName, QString filename);


  void query(QString query);
  QStringList queryLucene(const QString& queryString);
  QStringList queryMovies();
  void distantQueryLucene(const QString& host, const QString& queryString);


  Q_NOREPLY void quit();

 signals:
  void aboutToQuit();
};

} // namespace smewt

#endif // SMEWTD_H
